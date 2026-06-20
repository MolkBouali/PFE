"""
Service gestion des dossiers.
Creation avec numero unique, mise a jour du statut,
cycle de vie : en_cours -> en_attente_complement -> traite -> archive.
"""
from sqlalchemy.orm import Session
from backend.models.dossier import Dossier
from backend.schemas.dossier_schema import DossierCreate
import datetime, uuid

class DossierService:
    def __init__(self, db: Session):
        self.db = db

    def create(self, data: DossierCreate, agent_id: int) -> Dossier:
        numero = f"OACA-{datetime.date.today().year}-{str(uuid.uuid4())[:8].upper()}"
        dossier = Dossier(numero_dossier=numero, nom_demandeur=data.nom_demandeur,
                           identifiant_depositaire=data.identifiant_depositaire,
                           type_demande=data.type_demande, region=data.region,
                           statut="en_cours", agent_id=agent_id, date_depot=datetime.date.today())
        self.db.add(dossier)
        self.db.commit()
        self.db.refresh(dossier)
        return dossier

    def get_all(self, numero: str = None, demandeur: str = None, statut: str = None):
        query = self.db.query(Dossier)
        if numero and numero.strip():
            query = query.filter(Dossier.numero_dossier.ilike(f"%{numero.strip()}%"))
        if demandeur and demandeur.strip():
            query = query.filter(Dossier.nom_demandeur.ilike(f"%{demandeur.strip()}%"))
        if statut and statut.strip() and statut != "Tous":
            query = query.filter(Dossier.statut == statut.strip())
        return query.all()
    def get_by_id(self, dossier_id: int): return self.db.query(Dossier).filter(Dossier.id == dossier_id).first()

    def update(self, dossier_id: int, data: DossierCreate) -> Dossier:
        dossier = self.get_by_id(dossier_id)
        for k, v in data.dict().items():
            setattr(dossier, k, v)
        self.db.commit()
        self.db.refresh(dossier)
        return dossier

    def update_statut(self, dossier_id: int, statut: str):
        d = self.get_by_id(dossier_id)
        d.statut = statut
        self.db.commit()
