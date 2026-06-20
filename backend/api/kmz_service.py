"""Route generation KMZ. POST /documents/generate/kmz/{dossier_id}"""
from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from backend.services.kmz_service import KMZService
from backend.core.dependencies import get_db, get_current_user

router = APIRouter()

@router.get("/generate/kmz/{dossier_id}")
def generate_kmz(dossier_id: int, db: Session = Depends(get_db),
                 current_user=Depends(get_current_user)):
    """Genere le fichier KMZ depuis les coordonnees WGS84 validees."""
    path = KMZService(db).generate(dossier_id)
    return FileResponse(path, media_type="application/vnd.google-earth.kmz",
                        filename=f"localisation_{dossier_id}.kmz")
