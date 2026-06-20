# backend/modules/dea_config.py

AEROPORTS = {
    "Tunis-Carthage (DTTA)":        6.40,
    "Djerba-Zarzis (DTTJ)":         6.10,
    "Enfidha-Hammamet (DTNH)":      6.40,
    "Sfax-Thyna (DTTX)":           25.90,
    "Monastir-Habib Bourguiba (DTMB)": 2.74,
    "Tozeur-Nefta (DTTZ)":         87.47,
    "Gafsa-Ksar (DTTF)":          323.08,
    "Gabès-Matmata (DTTG)":       124.96,
    "Tabarka-Aïn Draham (DTKA)":   70.10,
    "Borj El Amri (DTTI)":         33.22,
}

SURFACES = [
    "Horizontale Intérieure",
    "Conique",
    "Approche — 1ère section",
    "Approche — 2ème section",
    "Approche — 3ème section",
    "Transition",
    "Montée au Décollage",
]

# True = la distance D est nécessaire pour cette surface
SURFACE_NEEDS_DISTANCE = {
    "Horizontale Intérieure":    False,
    "Conique":                   True,
    "Approche — 1ère section":   True,
    "Approche — 2ème section":   True,
    "Approche — 3ème section":   True,
    "Transition":                True,
    "Montée au Décollage":       True,
}