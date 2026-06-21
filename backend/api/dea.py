# backend/routes/dea.py

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional
from backend.modules.dea_engine import calculer_altitude_autorisee
from backend.modules.dea_config import AEROPORTS, SURFACES, SURFACE_NEEDS_DISTANCE
from backend.core.dependencies import get_current_user

router = APIRouter()

class DeaRequest(BaseModel):
    aeroport: str
    surface: str
    distance_m: Optional[float] = None

@router.get("/config")
def get_dea_config(current_user=Depends(get_current_user)):
    """Retourne la liste des aéroports, surfaces et règles distance."""
    return {
        "aeroports": AEROPORTS,
        "surfaces": SURFACES,
        "surface_needs_distance": SURFACE_NEEDS_DISTANCE,
    }

@router.post("/calculer")
def calculer_dea(req: DeaRequest, current_user=Depends(get_current_user)):
    """Calcule l'altitude autorisée selon les paramètres DEA."""
    return calculer_altitude_autorisee(
        req.aeroport, req.surface, req.distance_m
    )