from pprint import pprint

from biomodels_client.database import SensorStore

db_file = "wearables.sqlite"  # see 01_import_apple_health.py
dt_start = "2026-05-17 08:00"
dt_end = "2026-06-17 10:00"

# read sqlite
db = SensorStore(db_file)

# wearable-source with most HR values in time range
db.select_best_heart_rate_source(
    start=dt_start,
    end=dt_end,
)

# heart-rate values for time range
hr = db.select_heart_rate(
    start=dt_start,
    end=dt_end,
)
print(hr.head())

# estimate hr rest and hr max from sensor data
hr_ruhe = db.estimate_hr_rest(
    months = 3,
    night_start = 2,
    night_end = 5,
    lower_pct = 0.05,
)

hr_max = db.estimate_hr_max(
    months = 12,
    n_top = 3,
)

# custom SQLite query
sources = db.query(
    """
    SELECT
        source_name,
        COUNT(*) AS n,
        MIN(time_start) AS date_min,
        MAX(time_end) AS date_max
    FROM measurements
    GROUP BY source_name
    ORDER BY n DESC
    """
)

pprint(sources)
