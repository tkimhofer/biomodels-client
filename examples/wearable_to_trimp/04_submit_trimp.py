from pprint import pprint

from biomodels_client.client import BioModelleClient
from biomodels_client.database import SensorStore

db_file = "wearables.sqlite"

dt_start = "2026-06-17 06:00"
dt_end = "2026-06-18 23:00"

# open previously imported sensor database
db = SensorStore(db_file)

# estimate heart-rate characteristics
hr_ruhe = db.estimate_hr_rest(months=12)
hr_max = db.estimate_hr_max(months=24)

# instantiate biomodelle client
client = BioModelleClient()

# prepare trimp payload from sensor data
payload = db.trimp_payload(
    start=dt_start,
    end=dt_end,
)

# submit payload to the biomodelle trimp endpoint
result = client.trimp(
    **payload,
    geschlecht="m",
    hr_ruhe=hr_ruhe,
    hr_max=hr_max,
)

pprint(result, compact=True)