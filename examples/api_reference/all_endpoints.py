from pprint import pprint

from biomodels_client.client import BioModelleClient
from biomodels_client.fixtures import P1, TRIMP_EXAMPLE, CRITICAL_SPEED_EXAMPLE

client = BioModelleClient()

# body mass index & surface area
anthro = client.bmi_bsa(
    gewicht_kg=P1["gewicht_kg"],
    groesse_cm=P1["groesse_cm"],
)

pprint(anthro)


# training impulse (Banister)
trimp = client.trimp(
    hr_bpm=TRIMP_EXAMPLE["hr_bpm"],
    zeit_s=TRIMP_EXAMPLE["zeit_s"],
    geschlecht=P1["geschlecht"],
    hr_ruhe=P1["hr_ruhe"],
    hr_max=P1["hr_max"],
)

pprint(trimp)

# critical speed (Monod & Scherrer)
cs = client.critical_speed(
    laufleistung=CRITICAL_SPEED_EXAMPLE["laufleistung"],
)

pprint(cs)


# LOINC mit deutscher Term-Übersetzung
loinc = client.loinc("8867-4")

pprint(loinc)

