"""
Service archivage.
Recherche multi-criteres (numero, deposant, statut),
acces au detail complet d un dossier archive.
"""
from sqlalchemy.orm import Session
from backend.models.dossier import Dossier
from typing import Optional

class ArchiveService:
    def __init__(self, db: Session):
        self.db = db

    def search(self, numero: Optional[str], deposant: Optional[str], statut: Optional[str]):
        q = self.db.query(Dossier)
        
        # Nettoyage et filtrage robuste
        clean_numero = numero.strip() if numero else None
        clean_deposant = deposant.strip() if deposant else None
        clean_statut = statut.strip() if statut else None

        if clean_numero:
            q = q.filter(Dossier.numero_dossier.ilike(f"%{clean_numero}%"))
        
        if clean_deposant:
            q = q.filter(Dossier.nom_demandeur.ilike(f"%{clean_deposant}%"))
        
        # On filtre par statut seulement s'il est précisé et différent de "Tous"
        if clean_statut and clean_statut.lower() != "tous":
            q = q.filter(Dossier.statut == clean_statut)
            
        return q.all()

    def get_detail(self, dossier_id: int):
        return self.db.query(Dossier).filter(Dossier.id == dossier_id).first()
