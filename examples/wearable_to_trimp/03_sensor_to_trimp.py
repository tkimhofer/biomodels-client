from pprint import pprint

from biomodels_client.database import SensorStore

db_file = "wearables.sqlite"

dt_start = "2026-06-17 06:00"
dt_end = "2026-06-18 23:00"

# open previously imported sensor database
db = SensorStore(db_file)

# prepare TRIMP endpoint payload from wearable data
# (uses the hr source with the most observations in the requested time range)
payload = db.trimp_payload(
    start=dt_start,
    end=dt_end,
)

# payload summary
pprint({
    "n_hr_values": len(payload["hr_bpm"]),
    "n_time_values": len(payload["zeit_s"]),
    "hr_preview": payload["hr_bpm"][:5],
    "zeit_preview": payload["zeit_s"][:5],
})

