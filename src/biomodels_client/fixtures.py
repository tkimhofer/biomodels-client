P1 = {
    # anthropometry
    "gewicht_kg": 90,
    "groesse_cm": 180,
    "taille_cm": 92,
    "huefte_cm": 101,
    "koerperfett_prozent": 18,

    # demographics
    "alter": 44,
    "geschlecht": "m",

    # cardiovascular
    "hr_ruhe": 54,
    "hr_max": 178,

    # lipids
    "vai_tg_mmol_l": 1.1,
    "vai_hdl_mmol_l": 1.4,

    # activity
    "aktivitaetsfaktor": 1.7,

    # VO2max
    "cooper_distanz_m": 2800,
    "rockport_zeit_s": 780,
    "rockport_hr_ende_bpm": 128,
}

TRIMP_EXAMPLE = {
    "hr_bpm": [100, 120, 140, 160],
    "zeit_s": [300, 300, 300, 300],
}

CRITICAL_SPEED_EXAMPLE = {
    "laufleistung": [
        {"strecke_m": 700, "zeit_s": 180},  # 3 min
        {"strecke_m": 1350, "zeit_s": 360},  # 6 min
        {"strecke_m": 2500, "zeit_s": 720},  # 12 min
    ]
}