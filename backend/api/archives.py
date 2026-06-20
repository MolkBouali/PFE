"""Routes archives. GET /archives, GET /archives/{id}"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from backend.services.archive_service import ArchiveService
from backend.core.dependencies import get_db, get_current_user
from typing import Optional

router = APIRouter()

@router.get("/")
def list_archives(numero: Optional[str] = Query(None), deposant: Optional[str] = Query(None),
                  statut: Optional[str] = Query(None),
                  db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return ArchiveService(db).search(numero, deposant, statut)

@router.get("/{dossier_id}")
def get_archive_detail(dossier_id: int, db: Session = Depends(get_db),
                       current_user=Depends(get_current_user)):
    return ArchiveService(db).get_detail(dossier_id)
