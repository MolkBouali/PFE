# backend/modules/dea_config.py

AEROPORTS = {
    "Aéroport International de Tunis-Carthage":        6.40,
    "Aéroport International de Djerba-Zarzis":         6.10,
    "Aéroport International d'Enfidha-Hammamet":      6.40,
    "Aéroport International de Sfax-Thyna":           25.90,
    "Aéroport International de Monastir Habib-Bourguiba": 2.74,
    "Aéroport International de Tozeur-Nefta":         87.47,
    "Aéroport International de Gafsa-Ksar":          323.08,
    "Aéroport International de Gabès-Matmata":       124.96,
    "Aéroport International de Tabarka-Aïn Draham":   70.10,
    "Aéroport Borj El Amri":         33.22,
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