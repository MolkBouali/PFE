# backend/modules/dea_engine.py

from .dea_config import AEROPORTS

def calculer_altitude_autorisee(
    aeroport: str,
    surface: str,
    distance_m: float = None
) -> dict:
    """
    Calcule l'altitude maximale autorisée selon la surface choisie.
    Retourne: { alt_autorisee, formule_appliquee, alt_ref, erreur }
    """
    alt_ref = AEROPORTS.get(aeroport)
    if alt_ref is None:
        return {"erreur": f"Aéroport inconnu : {aeroport}"}

    s = surface
    D = distance_m
    alt = None
    formule = ""

    if s == "Horizontale Intérieure":
        alt = alt_ref + 45
        formule = f"Alt_Ref ({alt_ref}) + 45"

    elif s == "Conique":
        if D is None:
            return {"erreur": "Distance D requise pour la surface Conique."}
        alt = (alt_ref + 45) + (D * 0.05)
        formule = f"(Alt_Ref ({alt_ref}) + 45) + (D ({D}) × 0.05)"

    elif s == "Approche — 1ère section":
        if D is None:
            return {"erreur": "Distance D requise."}
        if D <= 3000:
            alt = alt_ref + (D * 0.02)
            formule = f"Alt_Ref ({alt_ref}) + (D ({D}) × 0.02)"
        else:
            return {"erreur": "D > 3000 m — utilisez la 2ème section."}

    elif s == "Approche — 2ème section":
        if D is None:
            return {"erreur": "Distance D requise."}
        if 3000 < D <= 6600:
            alt = alt_ref + 60 + ((D - 3000) * 0.025)
            formule = f"Alt_Ref ({alt_ref}) + 60 + ((D ({D}) - 3000) × 0.025)"
        else:
            return {"erreur": "D doit être entre 3000 et 6600 m."}

    elif s == "Approche — 3ème section":
        if D is None:
            return {"erreur": "Distance D requise."}
        if 6600 < D <= 15000:
            alt = 150
            formule = "Alt_Autorisée = 150 m (fixe pour 3ème section)"
        else:
            return {"erreur": "D doit être entre 6600 et 15000 m."}

    elif s == "Transition":
        if D is None:
            return {"erreur": "Distance D requise."}
        alt = alt_ref + (D * 0.143)
        formule = f"Alt_Ref ({alt_ref}) + (D ({D}) × 0.143)"

    elif s == "Montée au Décollage":
        if D is None:
            return {"erreur": "Distance D requise."}
        alt = alt_ref + (D * 0.016)
        formule = f"Alt_Ref ({alt_ref}) + (D ({D}) × 0.016)"

    else:
        return {"erreur": f"Surface inconnue : {surface}"}

    return {
        "alt_ref":          alt_ref,
        "surface":          surface,
        "distance_m":       D,
        "alt_autorisee":    round(alt, 2),
        "formule_appliquee": formule,
        "erreur":           None,
    }