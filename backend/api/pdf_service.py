"""Route generation PDF. POST /documents/generate/pdf/{dossier_id}"""
from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from backend.schemas.decision_schema import AvisValidationRequest
from backend.services.pdf_service import PDFService
from backend.core.dependencies import get_db, get_current_user

router = APIRouter()

@router.post("/generate/pdf/{dossier_id}")
def generate_pdf(dossier_id: int, data: AvisValidationRequest,
                 db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Genere l avis officiel PDF depuis les validations DER/DTA/DANA/DNA."""
    path = PDFService(db).generate(dossier_id, data, current_user.id)
    return FileResponse(path, media_type="application/pdf",
                        filename=f"avis_oaca_{dossier_id}.pdf")
