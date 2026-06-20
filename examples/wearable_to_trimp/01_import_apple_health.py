
from biomodels_client.database import SensorStore
from biomodels_client.importers.apple_health import AppleHealthImporter

export_file = '/Users/tk/Downloads/export 3/apple_health_export/export.xml'#"PATH/TO/apple_health_export/export.xml"
db_file = "wearables.sqlite"

db = SensorStore(db_file)

summary = AppleHealthImporter(export_file).write_to(db)

print(summary)
