"""Schemas Pydantic moteur decisionnel et avis."""
from pydantic import BaseModel
from typing import Optional

class EtudeRequest(BaseModel):
    aeroport: str
    type_surface: str
    type_objet: str
    altitude_sol: float
    altitude_finale: float
    hauteur_demandee: float
    distance_piste: Optional[float] = None

class DecisionResponse(BaseModel):
    type_avis: str
    hauteur_max_autorisee: float
    ecart_calcule: float
    balisage_requis: bool

class AvisValidationRequest(BaseModel):
    validation_der: bool
    validation_dta: bool
    validation_dana: bool
    validation_dna: bool
    justification: Optional[str] = None
