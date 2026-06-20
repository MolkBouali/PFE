"""Routes HTTP dossiers. GET/POST /dossiers, GET/PUT /dossiers/{id}"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.schemas.dossier_schema import DossierCreate, DossierResponse
from backend.services.dossier_service import DossierService
from backend.core.dependencies import get_db, get_current_user
from typing import List

router = APIRouter()

@router.get("/", response_model=List[DossierResponse])
def list_dossiers(
    numero: str = None, 
    demandeur: str = None, 
    statut: str = None, 
    db: Session = Depends(get_db), 
    current_user=Depends(get_current_user)
):
    return DossierService(db).get_all(numero=numero, demandeur=demandeur, statut=statut)

@router.post("/", response_model=DossierResponse, status_code=201)
def create_dossier(data: DossierCreate, db: Session = Depends(get_db),
                   current_user=Depends(get_current_user)):
    return DossierService(db).create(data, current_user.id)

@router.get("/{dossier_id}", response_model=DossierResponse)
def get_dossier(dossier_id: int, db: Session = Depends(get_db),
                current_user=Depends(get_current_user)):
    d = DossierService(db).get_by_id(dossier_id)
    if not d:
        raise HTTPException(status_code=404, detail="Dossier non trouve")
    return d

@router.put("/{dossier_id}", response_model=DossierResponse)
def update_dossier(dossier_id: int, data: DossierCreate, db: Session = Depends(get_db),
                   current_user=Depends(get_current_user)):
    return DossierService(db).update(dossier_id, data)
