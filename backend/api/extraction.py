"""Route extraction. POST /extraction/extract/{dossier_id}"""
import os
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from backend.schemas.extraction_schema import (
    ExtractionResult, ValidationRequest, ValidationResult, ConfirmationRequest
)
from backend.services.extraction_service import ExtractionService
from backend.services.pdf_service import PDFService
from backend.core.dependencies import get_db, get_current_user

router = APIRouter()


@router.post("/extract/{dossier_id}", response_model=ExtractionResult)
async def extract_coordinates(dossier_id: int, file: UploadFile = File(...),
                                db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Pipeline: ArUco -> ROI -> PaddleOCR -> Preview results."""
    if file.content_type not in ["image/png", "image/jpeg", "application/pdf"]:
        raise HTTPException(status_code=400, detail="Format non supporte (PNG, JPG, PDF)")
    return ExtractionService(db).preview_extract(dossier_id, await file.read(), file.filename)


@router.post("/validate", response_model=ValidationResult)
async def validate_coordinates(req: ValidationRequest, db: Session = Depends(get_db),
                                 current_user=Depends(get_current_user)):
    """
    Valide les coordonnées DMS côté serveur (sans persistance).
    Utilise le même code regex que le pipeline OCR.
    Retourne le statut de validation pour chaque point.
    """
    print(f"DEBUG: /validate received {len(req.points)} points")
    for i, p in enumerate(req.points):
        print(f"DEBUG: Point {i}: {p}")
        
    result = ExtractionService(db).validate_dms_points(
        [p.model_dump() for p in req.points]
    )
    print(f"DEBUG: /validate result nb_total={result.get('nb_total')}, nb_valides={result.get('nb_valides')}")
    return result


@router.post("/confirm")
async def confirm_extraction(req: ConfirmationRequest, db: Session = Depends(get_db),
                                current_user=Depends(get_current_user)):
    """
    Sauvegarde les points validés en BDD + génère le KMZ automatiquement.
    Retourne le statut, l'altitude finale max, et les infos du KMZ.
    """
    # Utilisation du DTO validé par Pydantic
    result = ExtractionService(db).confirm_extraction(req.formulaire_id, [p.model_dump() for p in req.points])
    return result


@router.post("/generate-complement/{dossier_id}")
async def generate_complement(dossier_id: int, db: Session = Depends(get_db), 
                               current_user=Depends(get_current_user)):
    """Génère le document de demande de complément de coordonnées au format DMS."""
    try:
        file_path = PDFService(db).generate_complement(dossier_id)
        return FileResponse(
            path=file_path, 
            filename=os.path.basename(file_path), 
            media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la génération: {str(e)}")