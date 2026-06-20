from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from backend.services.decision_engine import decision_engine

router = APIRouter()

class AnalysisRequest(BaseModel):
    aeroport: str
    surface: str
    objet: str
    distance: Optional[float] = None
    altitude_finale: Optional[float] = 160.0

@router.post("/analyze")
async def analyze_height(request: AnalysisRequest):
    try:
        # Convert Pydantic model to dict for the service
        data = request.dict()
        result = decision_engine.calculate_max_height(data)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'analyse : {str(e)}")