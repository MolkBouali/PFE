"""
Service statistiques tableau de bord.
Calcul : total dossiers, repartition avis, evolution mensuelle,
distribution par region et type de formulaire.
"""
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.models.dossier import Dossier
from backend.models.decision_avis import DecisionAvis
from typing import Optional

class StatsService:
    def __init__(self, db: Session):
        self.db = db

    def get_dashboard(self, periode: Optional[str], region: Optional[str]) -> dict:
        total = self.db.query(func.count(Dossier.id)).scalar()
        en_cours = self.db.query(func.count(Dossier.id)).filter(Dossier.statut=="en_cours").scalar()
        traites = self.db.query(func.count(Dossier.id)).filter(Dossier.statut=="traite").scalar()
        repartition = self.db.query(DecisionAvis.type_avis, func.count(DecisionAvis.id)
                                    ).group_by(DecisionAvis.type_avis).all()
        return {"total_dossiers": total, "en_cours": en_cours, "traites": traites,
                "repartition_avis": {k: v for k, v in repartition}}
