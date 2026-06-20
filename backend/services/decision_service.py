"""
Service moteur decisionnel.
Recupere les regles aeronautiques selon l aeroport et la surface,
calcule la hauteur maximale autorisee, compare avec la hauteur demandee,
produit le diagnostic : FAVORABLE / FAVORABLE_AVEC_BALISAGE / DEFAVORABLE.
"""
from sqlalchemy.orm import Session
from backend.models.etude_technique import EtudeTechnique
from backend.schemas.decision_schema import EtudeRequest, DecisionResponse
import datetime

REGLES = {
    "piste": {"hauteur_max": 45, "seuil_balisage": 30},
    "approche": {"hauteur_max": 100, "seuil_balisage": 60},
    "transition": {"hauteur_max": 150, "seuil_balisage": 100},
}

class DecisionService:
    def __init__(self, db: Session):
        self.db = db

    def analyse(self, dossier_id: int, data: EtudeRequest) -> DecisionResponse:
        regle = REGLES.get(data.type_surface, {"hauteur_max": 100, "seuil_balisage": 60})
        hauteur_max = regle["hauteur_max"]
        ecart = data.hauteur_demandee - hauteur_max
        if ecart <= 0:
            type_avis = "FAVORABLE"
        elif data.hauteur_demandee <= regle["seuil_balisage"] + hauteur_max:
            type_avis = "FAVORABLE_AVEC_BALISAGE"
        else:
            type_avis = "DEFAVORABLE"

        etude = EtudeTechnique(dossier_id=dossier_id, aeroport=data.aeroport,
                               type_surface=data.type_surface, type_objet=data.type_objet,
                               altitude_sol=data.altitude_sol, altitude_finale=data.altitude_finale,
                               hauteur_demandee=data.hauteur_demandee, distance_piste=data.distance_piste,
                               hauteur_max_autorisee=hauteur_max, ecart_calcule=ecart,
                               conformite=(ecart <= 0), date_enregistrement=datetime.datetime.now())
        self.db.add(etude)
        self.db.commit()
        return DecisionResponse(type_avis=type_avis, hauteur_max_autorisee=hauteur_max,
                                ecart_calcule=ecart, balisage_requis=(type_avis=="FAVORABLE_AVEC_BALISAGE"))
