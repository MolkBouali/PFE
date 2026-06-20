"""
Dependances FastAPI injectees via Depends().
- get_db : fournit une session DB par requete, fermee automatiquement apres
- get_current_user : verifie le token JWT et retourne l utilisateur connecte
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from backend.database.connection import SessionLocal
from backend.core.security import decode_token
from backend.models.utilisateur import Utilisateur
from jose import JWTError

bearer_scheme = HTTPBearer()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
                     db: Session = Depends(get_db)) -> Utilisateur:
    try:
        payload = decode_token(credentials.credentials)
        user_id = int(payload.get("sub"))
    except (JWTError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token invalide")
    user = db.query(Utilisateur).filter(Utilisateur.id == user_id).first()
    if not user or not user.statut:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Acces refuse")
    return user
