import hashlib, json, zipfile
import xml.etree.ElementTree as ET
from decimal import Decimal
from uuid import uuid4
from pathlib import Path

def iso(ts: str) -> str:
    # Apple format: "YYYY-MM-DD HH:MM:SS ±HHMM/±HH:MM"
    ts = ts.replace(" +0000", "Z").replace(" -0000", "Z")
    # If not Z, convert " +0200" to "+02:00"
    if len(ts) >= 5 and (ts[-5] in ["+", "-"]) and ts[-3] != ":":
        ts = ts[:-5] + ts[-5:-2] + ":" + ts[-2:]
    ts = ts.replace(" ", "T", 1)
    return ts

def to_ucum(value: str, hk_unit: str, target_ucum: str) -> tuple[Decimal, str]:
    v = Decimal(value)

    if target_ucum == "kg" and hk_unit in ("lb", "lbs"):
        return (v * Decimal("0.45359237"), "kg")
    if target_ucum == "/min" and hk_unit in ("count/min", "beats/min"):
        return (v, "/min")
    if target_ucum == "mg/dL" and hk_unit == "mmol/L":  # glucose conversion (glucose factor ~18.016)
        return (v * Decimal("18.016"), "mg/dL")

    return (v, target_ucum or hk_unit)


# health kit to loinc + ucum
HK_TO_LOINC = {
    "HKQuantityTypeIdentifierBodyMass": {
        "type": "body_mass",
        "loinc": "29463-7",
        "ucum": "kg",
    },
    "HKQuantityTypeIdentifierBodyMassIndex": {
        "type": "bmi",
        "loinc": "39156-5",
        "ucum": "{score}",
    },
    "HKQuantityTypeIdentifierHeartRate": {
        "type": "heart_rate",
        "loinc": "8867-4",
        "ucum": "/min",
    },
    "HKQuantityTypeIdentifierBloodGlucose": {
        "type": "blood_glucose",
        "loinc": "2345-7",
        "ucum": "mg/dL",
    },
    "HKQuantityTypeIdentifierOxygenSaturation": {
        "type": "oxygen_saturation",
        "loinc": "59408-5",
        "ucum": "%",
    },
    "HKQuantityTypeIdentifierStepCount": {
        "type": "step_count",
        "loinc": "41950-7",
        "ucum": "{count}",
    },
}

class AppleHealthImporter:

    def __init__(self, path: str):
        self.path = Path(path)

        if self.path.suffix == ".zip":
            outdir = self.path.with_suffix("")

            if not outdir.exists():
                with zipfile.ZipFile(self.path) as zf:
                    zf.extractall(outdir)

            self.xml_path = next(
                p for p in outdir.rglob("export.xml")
            )

        else:
            self.xml_path = self.path

        self.ndjson_path = (
            self.xml_path.parent / "export_biomodels.ndjson"
        )

    def records(self):
        with self.xml_path.open("rb") as fh:
            yield from self._iter_records(fh)

    def observation(self, record, patient_ref="Patient/self"):
        hk = record["type"]

        if hk not in HK_TO_LOINC:
            return None

        if not record.get("value"):
            return None

        effective_time = record.get("endDate") or record.get("startDate")
        if not effective_time:
            return None

    def _iter_records(self, fh):
        context = ET.iterparse(fh, events=("end",))
        for event, elem in context:
            if elem.tag == "Record":
                yield {
                    "type": elem.attrib.get("type"),  # e.g. HKQuantityTypeIdentifierBodyMass
                    "unit": elem.attrib.get("unit"),  # e.g. "kg", "count/min", "mg/dL"
                    "value": elem.attrib.get("value"),
                    "startDate": elem.attrib.get("startDate"),
                    "endDate": elem.attrib.get("endDate"),
                    "sourceName": elem.attrib.get("sourceName"),
                    "sourceVersion": elem.attrib.get("sourceVersion"),
                    "device": elem.attrib.get("device"),
                }
                elem.clear()

    def measurement(self, record):
        hk = record["type"]

        if hk not in HK_TO_LOINC:
            return None

        if not record.get("value"):
            return None

        start_time = record.get("startDate")
        end_time = record.get("endDate") or start_time

        if not start_time:
            return None

        loinc = HK_TO_LOINC[hk]["loinc"]
        target_ucum = HK_TO_LOINC[hk]["ucum"]

        val, ucum = to_ucum(
            record["value"],
            record.get("unit"),
            target_ucum,
        )

        row = {
            "source": "apple_health",
            "source_file": str(self.xml_path),

            "provider": "Apple",
            "source_name": record.get("sourceName"),
            "source_version": record.get("sourceVersion"),
            "device": record.get("device"),

            "type": HK_TO_LOINC[hk].get("type"),
            "hk_type": hk,
            "loinc": loinc,

            "value": float(val),
            "unit": ucum,

            "time_start": iso(start_time),
            "time_end": iso(end_time),

            "workout_id": None,
        }

        row["record_hash"] = self._record_hash(row)
        return row

    def write_to(self, store):
        n_seen = 0
        n_inserted = 0

        for rec in self.records():
            row = self.measurement(rec)

            if row is None:
                continue

            n_seen += 1
            before = store.con.total_changes
            store.insert(row)
            after = store.con.total_changes

            if after > before:
                n_inserted += 1

        store.commit()

        return {
            "records_seen": n_seen,
            "records_inserted": n_inserted,
            "records_skipped": n_seen - n_inserted,
            "database": str(store.path),
        }

    def to_ndjson(self, patient_ref="Patient/self"):
        with open(self.ndjson_path, "w", encoding="utf-8") as out:
            for rec in self.records():
                obs = self.observation(rec, patient_ref=patient_ref)
                if obs:
                    out.write(json.dumps(obs, ensure_ascii=False) + "\n")

    def _record_hash(self, row: dict) -> str:
        key = {
            "source": row.get("source"),
            "hk_type": row.get("hk_type"),
            "value": row.get("value"),
            "unit": row.get("unit"),
            "time_start": row.get("time_start"),
            "time_end": row.get("time_end"),
            "source_name": row.get("source_name"),
            "device": row.get("device"),
        }

        raw = json.dumps(key, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()