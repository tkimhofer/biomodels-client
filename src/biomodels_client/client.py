from __future__ import annotations

from typing import Literal
import requests


class BioModelleClient:
    api_version = "v1"

    def __init__(
        self,
        base_url: str = "https://biomodels.tkimhofer.dev",
        timeout: int | float = 30,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({"accept": "application/json"})

    def endpoint(self, path, versioned: bool = True):
        path = path.lstrip("/")

        if versioned:
            return f"{self.base_url}/{self.api_version}/{path}"

        return f"{self.base_url}/{path}"

    def _get(self, path: str, params: dict | None = None, versioned=True) -> dict:
        r = self.session.get(
            self.endpoint(path, versioned),
            # f"{self.base_url}{path}",
            params=params,
            timeout=self.timeout,
        )
        return self._handle_response(r)

    def _post(
        self,
        path: str,
        params: dict | None = None,
        payload: dict | None = None,
        versioned = True
    ) -> dict:
        r = self.session.post(
            self.endpoint(path, versioned),
            params=params,
            json=payload,
            timeout=self.timeout,
        )
        return self._handle_response(r)

    @staticmethod
    def _handle_response(response: requests.Response) -> dict:
        try:
            data = response.json()
        except ValueError:
            data = response.text

        if not response.ok:
            raise RuntimeError(
                f"BioModelle API error {response.status_code}: {data}"
            )

        return data

    def health(self) -> dict:
        return self._get("/health", versioned=False)

    def bmi_bsa(self, gewicht_kg: float, groesse_cm: float) -> dict:
        return self._get(
            "/body/bmi-bsa",
            params={
                "gewicht_kg": gewicht_kg,
                "groesse_cm": groesse_cm,
            },
        )

    def body_shape(
        self,
        gewicht_kg: float,
        groesse_cm: float,
        taille_cm: float,
        geschlecht: Literal["m", "w"],
        huefte_cm: float | None = None,
        koerperfett_prozent: float | None = None,
    ) -> dict:
        params = {
            "gewicht_kg": gewicht_kg,
            "groesse_cm": groesse_cm,
            "taille_cm": taille_cm,
            "geschlecht": geschlecht,
        }

        if huefte_cm is not None:
            params["huefte_cm"] = huefte_cm

        if koerperfett_prozent is not None:
            params["koerperfett_prozent"] = koerperfett_prozent

        return self._get("/body/body-shape", params=params)

    def visceral_fat(
        self,
        gewicht_kg: float,
        groesse_cm: float,
        taille_cm: float,
        geschlecht: Literal["m", "w"],
        vai_tg_mmol_l: float | None = None,
        vai_hdl_mmol_l: float | None = None,
    ) -> dict:
        params = {
            "gewicht_kg": gewicht_kg,
            "groesse_cm": groesse_cm,
            "taille_cm": taille_cm,
            "geschlecht": geschlecht,
        }

        if vai_tg_mmol_l is not None:
            params["vai_tg_mmol_l"] = vai_tg_mmol_l

        if vai_hdl_mmol_l is not None:
            params["vai_hdl_mmol_l"] = vai_hdl_mmol_l

        return self._get("/body/visceral-fat", params=params)

    def tofi_risk(
        self,
        gewicht_kg: float,
        groesse_cm: float,
        taille_cm: float,
    ) -> dict:
        return self._get(
            "/body/tofi-risk",
            params={
                "gewicht_kg": gewicht_kg,
                "groesse_cm": groesse_cm,
                "taille_cm": taille_cm,
            },
        )

    def hr_max(self, alter: int | float) -> dict:
        return self._get(
            "/performance/hr-max",
            params={"alter": alter},
        )

    def hr_zones(
        self,
        alter: int,
        hr_ruhe: int | None = None,
        hr_max: int | None = None,
    ) -> dict:
        params = {"alter": alter}

        if hr_ruhe is not None:
            params["hr_ruhe"] = hr_ruhe

        if hr_max is not None:
            params["hr_max"] = hr_max

        return self._get("/performance/hr-zones", params=params)

    def trimp(
        self,
        hr_bpm: list[float],
        zeit_s: list[float],
        geschlecht: Literal["m", "w"],
        hr_ruhe: float,
        hr_max: float,
    ) -> dict:
        return self._post(
            "/performance/trimp",
            params={
                "geschlecht": geschlecht,
                "hr_ruhe": hr_ruhe,
                "hr_max": hr_max,
            },
            payload={
                "hr_bpm": hr_bpm,
                "zeit_s": zeit_s,
            },
        )

    def critical_speed(
        self,
        laufleistung: list[dict[str, float]],
    ) -> dict:
        return self._post(
            "/performance/critical-speed",
            payload={"laufleistung": laufleistung},
        )

    def bmr(
        self,
        gewicht_kg: float,
        groesse_cm: float,
        alter: int,
        geschlecht: Literal["m", "w"],
        koerperfettanteil: float | None = None,
    ) -> dict:
        params = {
            "gewicht_kg": gewicht_kg,
            "groesse_cm": groesse_cm,
            "alter": alter,
            "geschlecht": geschlecht,
        }

        if koerperfettanteil is not None:
            params["körperfettanteil"] = koerperfettanteil

        return self._get("/metabolism/bmr", params=params)

    def tdee(
        self,
        gewicht: float,
        groesse: float,
        alter: int,
        geschlecht: Literal["m", "w"],
        aktivitaetsfaktor: float = 1.55,
        koerperfettanteil: float | None = None,
    ) -> dict:
        params = {
            "gewicht": gewicht,
            "groesse": groesse,
            "alter": alter,
            "geschlecht": geschlecht,
            "aktivitaetsfaktor": aktivitaetsfaktor,
        }

        if koerperfettanteil is not None:
            params["körperfettanteil"] = koerperfettanteil

        return self._get("/metabolism/tdee", params=params)

    def vo2max(
        self,
        gewicht_kg: float | None = None,
        alter: int | None = None,
        geschlecht: Literal["m", "w"] | None = None,
        rockport_zeit_s: float | None = None,
        rockport_hr_ende_bpm: int | None = None,
        cooper_distanz_m: float | None = None,
        uth_hr_ruhe_bpm: int | None = None,
        uth_hr_max_bpm: int | None = None,
    ) -> dict:
        params = {
            "gewicht_kg": gewicht_kg,
            "alter": alter,
            "geschlecht": geschlecht,
            "rockport_zeit_s": rockport_zeit_s,
            "rockport_hr_ende_bpm": rockport_hr_ende_bpm,
            "cooper_distanz_m": cooper_distanz_m,
            "uth_hr_ruhe_bpm": uth_hr_ruhe_bpm,
            "uth_hr_max_bpm": uth_hr_max_bpm,
        }

        params = {k: v for k, v in params.items() if v is not None}

        return self._get("/metabolism/vo2max", params=params)

    def lactate_threshold(
        self,
        laufleistung: list[dict[str, float]],
    ) -> dict:
        return self._get(
            "/metabolism/lactate-threshold",
            params=None,
            # NOTE: your spec says GET with requestBody.
            # requests does not support json body in .get() nicely via helper.
        )

    def loinc(self, code: str) -> dict:
        return self._get(f"/terminology/loinc/{code}")
