import sys
from biomodels_client.database import SensorStore
from biomodels_client.importers.apple_health import AppleHealthImporter
from biomodels_client.client import BioModelleClient


export_file = "PATH/TO/apple_health_export/export.xml"
db_file = "wearables.sqlite"

db = SensorStore(db_file)

summary = AppleHealthImporter(export_file).write_to(db)

print(summary)



db = SensorStore(db_file)

AppleHealthImporter(export_file).write_to(db)

payload = db.trimp_payload(
    start="2026-06-17 06:00",
    end="2026-06-18 23:00",
)

client = BioModelleClient()

result = client.trimp(
    **payload,
    geschlecht="m",
    hr_ruhe=db.estimate_resting_hr(months=12),
    hr_max=db.estimate_hr_max(months=24),
)