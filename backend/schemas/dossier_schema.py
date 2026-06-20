"""Schemas Pydantic dossiers."""
from pydantic import BaseModel
from typing import Optional
from datetime import date

class DossierCreate(BaseModel):
    nom_demandeur: str
    identifiant_depositaire: str
    type_demande: str
    region: Optional[str] = None
    observations: Optional[str] = None

class DossierResponse(BaseModel):
    id: int
    numero_dossier: str
    nom_demandeur: str
    region: Optional[str] = None
    type_demande: Optional[str] = None
    statut: str
    avis: Optional[str] = None
    complement: Optional[str] = None
    date_depot: Optional[date] = None
    class Config:
        from_attributes = True
