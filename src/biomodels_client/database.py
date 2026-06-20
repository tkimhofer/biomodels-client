# src/biomodels_client/database.py
from __future__ import annotations

import sqlite3
from pathlib import Path
import pandas as pd
from typing import Union, Optional
import unicodedata

class SensorStore:

    def __init__(self, path: Union[str, Path] = "wearables.sqlite"):
        self.path = Path(path)

        self.con = sqlite3.connect(self.path)
        self.con.row_factory = sqlite3.Row

        self._create_schema()

    def _create_schema(self):
        self.con.execute("""
        CREATE TABLE IF NOT EXISTS measurements (
            id INTEGER PRIMARY KEY,
            
            record_hash TEXT UNIQUE,

            source TEXT,
            source_file TEXT,

            provider TEXT,
            source_name TEXT,
            source_version TEXT,
            device TEXT,

            type TEXT,
            hk_type TEXT,
            loinc TEXT,

            value REAL,
            unit TEXT,

            time_start TEXT,
            time_end TEXT,

            workout_id TEXT
        )
        """)

        self.con.execute("""
        CREATE INDEX IF NOT EXISTS idx_measurements_type
        ON measurements(type)
        """)

        self.con.execute("""
        CREATE INDEX IF NOT EXISTS idx_measurements_time
        ON measurements(time_start)
        """)

        self.con.commit()

    @staticmethod
    def _clean_text(value):
        if value is None:
            return None

        value = unicodedata.normalize("NFKC", value)
        value = value.replace("\xa0", " ")
        value = " ".join(value.split())

        return value

    def insert(self, record: dict):

        source_name = self._clean_text(record.get("source_name"))
        device = self._clean_text(record.get("device"))

        self.con.execute("""
        INSERT OR IGNORE INTO measurements (
            record_hash,
            source,
            source_file,
            provider,
            source_name,
            source_version,
            device,
            type,
            hk_type,
            loinc,
            value,
            unit,
            time_start,
            time_end,
            workout_id
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            record.get("record_hash"),
            record.get("source"),
            record.get("source_file"),
            record.get("provider"),
            source_name,
            record.get("source_version"),
            device,
            record.get("type"),
            record.get("hk_type"),
            record.get("loinc"),
            record.get("value"),
            record.get("unit"),
            record.get("time_start"),
            record.get("time_end"),
            record.get("workout_id"),
        ))

    def commit(self):
        self.con.commit()

    def close(self):
        self.con.close()


    def select(
        self,
        measurement_type: str,
        start: Optional[str] = None,
        end: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Retrieve measurements of a specified type.

        Parameters
        ----------
        measurement_type : str
            Measurement type (e.g. "heart_rate", "body_mass", "oxygen_saturation").
        start, end : str, optional
            Start and end datetime filters in format "YYYY-MM-DD HH:MM".

        Returns
        -------
        pd.DataFrame
            Measurements ordered by time.
        """

        sql = """
        SELECT *
        FROM measurements
        WHERE type = ?
        """

        params = [measurement_type]

        if start:
            sql += " AND time_start >= ?"
            params.append(start)

        if end:
            sql += " AND time_start <= ?"
            params.append(end)

        sql += " ORDER BY time_start"

        return pd.read_sql_query(
            sql,
            self.con,
            params=params,
            parse_dates=["time_start", "time_end"],
        )

    def select_best_heart_rate_source(
            self,
            start: str,
            end: str,
    ) -> dict[str, any]:
        """
        Return the heart-rate source and device contributing the
        largest number of measurements in a specified time range.

        Parameters
        ----------
        start, end : str, optional
            Start and end datetime filters in format "YYYY-MM-DD HH:MM".
        """

        sql = """
        SELECT
            COALESCE(source_name, '') AS source_name,
            COALESCE(device, '') AS device,
            COUNT(*) AS n
        FROM measurements
        WHERE type = 'heart_rate'
          AND time_start >= ?
          AND time_start <= ?
        GROUP BY source_name, device
        ORDER BY n DESC
        LIMIT 1
        """

        row = self.con.execute(sql, (start, end)).fetchone()

        if row is None:
            raise ValueError("No heart-rate measurements found in selected time range.")

        return {
            "source_name": row["source_name"],
            "device": row["device"],
            "n_werte":  row["n"],
        }

        # return row["source_name"], row["device"], row["n"]

    def select_heart_rate(
            self,
            start: Optional[str] = None,
            end: Optional[str] = None,
            source_name: Optional[str] = None,
            device: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Retrieve heart-rate measurements.

        Parameters
        ----------
        start, end : str, optional
            Inclusive datetime filters (e.g. "2026-06-17 08:00").
        source_name : str, optional
            Restrict results to a specific source.
        device : str, optional
            Restrict results to a specific device.

        Returns
        -------
        pd.DataFrame
            Heart-rate measurements ordered by time.
        """

        sql = """
        SELECT *
        FROM measurements
        WHERE type = 'heart_rate'
        """

        params = []

        if start:
            sql += " AND time_start >= ?"
            params.append(start)

        if end:
            sql += " AND time_start <= ?"
            params.append(end)

        if source_name is not None:
            sql += " AND COALESCE(source_name, '') = ?"
            params.append(source_name)

        if device is not None:
            sql += " AND COALESCE(device, '') = ?"
            params.append(device)

        sql += " ORDER BY time_start"

        return pd.read_sql_query(
            sql,
            self.con,
            params=params,
            parse_dates=["time_start", "time_end"],
        )

    def select_body_mass(self):

        return self.select(
            measurement_type="body_mass"
        )

    def trimp_payload(
            self,
            start: str,
            end: str,
            max_gap_s: float = 10 * 60,
    ) -> dict:

        """
            Prepare a TRIMP endpoint payload from heart-rate measurements.

            Heart-rate records are selected from the source/device with the
            highest number of observations within the requested time range.
            Measurements are ordered chronologically and converted into
            heart-rate/time interval pairs suitable for submission to the
            BioModelle TRIMP endpoint.

            Intervals larger than `max_gap_s` are discarded to avoid assigning
            excessive duration to isolated measurements separated by long
            recording gaps.

            Parameters
            ----------
            start : str
                Start datetime.
            end : str
                End datetime.
            max_gap_s : float, default=600
                Maximum allowed interval between consecutive measurements [s].

            Returns
            -------
            dict
                Dictionary containing:

                - hr_bpm : list[float]
                    Heart-rate values [bpm].
                - zeit_s : list[float]
                    Corresponding interval durations [s].

            Raises
            ------
            ValueError
                If insufficient measurements are available or no valid
                intervals remain after filtering.
            """

        hr_source = self.select_best_heart_rate_source(
            start=start,
            end=end,
        )

        df = self.select_heart_rate(
            start=start,
            end=end,
            source_name=hr_source["source_name"],
            device=hr_source["device"],
        )

        if len(df) < 2:
            raise ValueError("At least two heart-rate measurements required.")

        df = df.copy()
        df["time_start"] = pd.to_datetime(df["time_start"], utc=True, errors="coerce")
        df = df.dropna(subset=["time_start", "value"])

        df = df.sort_values("time_start").reset_index(drop=True)

        df["zeit_s"] = (
            df["time_start"]
            .shift(-1)
            .sub(df["time_start"])
            .dt.total_seconds()
        )

        df = df.iloc[:-1]
        df = df[
            (df["zeit_s"] > 0)
            & (df["zeit_s"] <= max_gap_s)
            ]

        if len(df) == 0:
            raise ValueError("No valid positive time intervals found.")

        return {
            "hr_bpm": df["value"].astype(float).tolist(),
            "zeit_s": df["zeit_s"].astype(float).tolist(),
        }

    def query(self, sql: str, params=None) -> pd.DataFrame:

        if params is None:
            params = []

        return pd.read_sql_query(
            sql,
            self.con,
            params=params,
        )

    def execute(self, sql: str, params=None):

        if params is None:
            params = []

        cur = self.con.execute(sql, params)
        self.con.commit()

        return cur

    def estimate_hr_rest(
            self,
            months: int = 12,
            night_start: int = 2,
            night_end: int = 5,
            lower_pct: float = 0.05,
    ) -> float:

        """
            Estimate resting heart rate from wearable heart-rate measurements.

            Uses measurements recorded during the night (default: 02:00-05:59)
            within the last `months` months. The estimate is calculated as the
            mean of the lowest `lower_pct` fraction of night-time heart-rate
            values.

            Parameters
            ----------
            months : int, default=12
                Number of months to consider.
            night_start : int, default=2
                Start hour of the night-time window (24 h clock).
            night_end : int, default=5
                End hour of the night-time window (24 h clock).
            lower_pct : float, default=0.05
                Fraction of lowest night-time values used for estimation.

            Returns
            -------
            float
                Estimated resting heart rate [bpm].
            """

        sql = f"""
        WITH recent_hr AS (
            SELECT value, time_start
            FROM measurements
            WHERE type = 'heart_rate'
              AND value IS NOT NULL
              AND time_start >= datetime('now', '-{months} months')
        ),
        night_hr AS (
            SELECT value
            FROM recent_hr
            WHERE CAST(strftime('%H', time_start) AS INTEGER)
                  BETWEEN {night_start} AND {night_end}
        ),
        lowest_pct AS (
            SELECT value
            FROM night_hr
            ORDER BY value
            LIMIT (
                SELECT MAX(
                    1,
                    CAST(COUNT(*) * {lower_pct} AS INTEGER)
                )
                FROM night_hr
            )
        )
        SELECT AVG(value) AS hr_ruhe_bpm
        FROM lowest_pct
        """

        row = self.con.execute(sql).fetchone()

        if row is None or row[0] is None:
            raise ValueError(
                "Unable to estimate resting heart rate."
            )

        return round(float(row[0]), 1)

    def estimate_hr_max(
            self,
            months: int = 12,
            n_top: int = 20,
    ) -> int:
        """
        Estimate maximum heart rate from wearable heart-rate measurements.

        Uses measurements recorded within the last `months` months and
        estimates HRmax from the highest observed heart-rate values.
        Rather than returning the absolute maximum, which may be affected
        by measurement artefacts or transient spikes, the estimate is
        calculated as the minimum value among the `n_top` highest
        heart-rate measurements.

        Parameters
        ----------
        months : int, default=12
            Number of months of heart-rate data to consider.

        n_top : int, default=20
            Number of highest heart-rate values used for estimation.
            Larger values produce more conservative estimates.

        Returns
        -------
        int
            Estimated maximum heart rate [bpm].

        Raises
        ------
        ValueError
            If fewer than `n_top` heart-rate measurements are available.
        """

        sql = """
        WITH recent_hr AS (
            SELECT value
            FROM measurements
            WHERE type = 'heart_rate'
              AND value IS NOT NULL
              AND time_start >= datetime('now', ?)
        ),
        top_hr AS (
            SELECT value
            FROM recent_hr
            ORDER BY value DESC
            LIMIT ?
        )
        SELECT
            COUNT(*) AS n_available,
            (
                SELECT MIN(value)
                FROM top_hr
            ) AS hr_max_bpm
        FROM recent_hr
        """

        row = self.con.execute(
            sql,
            (f"-{months} months", n_top)
        ).fetchone()

        n = row["n_available"]

        if n < n_top:
            raise ValueError(
                f"Insufficient heart-rate measurements for HRmax estimation. "
                f"Found {n} values in the last {months} months, "
                f"but at least {n_top} are required."
            )

        return int(round(float(row["hr_max_bpm"])))

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.commit()
        self.close()