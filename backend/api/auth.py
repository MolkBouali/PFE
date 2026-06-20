"""Routes HTTP authentification. POST /auth/login, POST /auth/logout, GET /auth/me"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.schemas.auth_schema import LoginRequest, TokenResponse
from backend.services.auth_service import AuthService
from backend.core.dependencies import get_db, get_current_user

router = APIRouter()

@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Authentifie un agent et retourne un token JWT."""
    token = AuthService(db).authenticate(request.identifiant, request.mot_de_passe)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Identifiant ou mot de passe incorrect")
    return token

@router.post("/logout")
def logout(current_user=Depends(get_current_user)):
    return {"message": "Deconnexion reussie"}

@router.get("/me")
def get_me(current_user=Depends(get_current_user)):
    return current_user
