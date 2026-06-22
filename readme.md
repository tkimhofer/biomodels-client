# Biomodels Client

Python tools for importing wearable sensor data and interacting with the Biomodels API.

The package provides utilities for importing, querying and analysing sensor data, preparing API payloads, 
and submitting requests to the BioModelle API.

https://biomodels.tkimhofer.dev/swagger


### Features
* Import Apple Health exports (`"export.xml"` or `.zip`)
* Query and explore sensor data using pandas and SQL
* Prepare API payloads directly from sensor measurements
* Submit requests to the BioModelle API

### Installation

```bash
pip install biomodels-client
```


## Quick Start

### Apple Health Export
Open the **Health** app on iPhone, tap the profile picture, select **Export All Health Data**. 
The generated ZIP archive contains an `export.xml` file that can be imported by `biomodels-client`.

### 1. Import Apple Health data

The importer accepts both `export.xml` files and Apple Health ZIP exports.

```python
from biomodels_client.database import SensorStore
from biomodels_client.importers.apple_health import AppleHealthImporter

db = SensorStore("wearables.sqlite")

AppleHealthImporter(
    "/path/to/apple_health_export/export.xml"
).write_to(db)
```

### 2. Explore sensor data

```python
from biomodels_client.database import SensorStore

db = SensorStore("wearables.sqlite")

sources = db.query("""
SELECT
    source_name,
    COUNT(*) AS n,
    MIN(time_start) AS date_min,
    MAX(time_end) AS date_max
FROM measurements
GROUP BY source_name
ORDER BY n DESC
""")

print(sources)
```

### 3. Calculate TRIMP from wearable data

```python
from biomodels_client.client import BioModelleClient
from biomodels_client.database import SensorStore

db = SensorStore("wearables.sqlite")

hr_ruhe = db.estimate_hr_rest(months=12)
hr_max = db.estimate_hr_max(months=24)

payload = db.trimp_payload(
    start="2026-06-17 06:00",
    end="2026-06-18 23:00",
)

client = BioModelleClient()

result = client.trimp(
    **payload,
    geschlecht="m",
    hr_ruhe=hr_ruhe,
    hr_max=hr_max,
)

print(result)
```

## Example Scripts

### Wearable Sensor Workflow

```text
examples/
└── wearable_to_trimp/
    ├── 01_import_apple_health.py
    ├── 02_inspect_sensor_store.py
    ├── 03_sensor_to_trimp.py
    └── 04_submit_trimp.py
```

### API Reference

```text
examples/
└── api_reference/
    └── all_endpoints.py
```

## SensorStore

The `SensorStore` class provides:

```python
db.select_heart_rate(...)
db.select_best_heart_rate_source(...)

db.estimate_hr_rest(...)
db.estimate_hr_max(...)

db.trimp_payload(...)

db.query(...)
db.execute(...)
```

for exploration and preparation of wearable sensor data.
