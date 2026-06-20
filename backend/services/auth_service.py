"""
Service authentification.
Verifie les identifiants, gere le hachage mot de passe et les tokens JWT.
"""
from sqlalchemy.orm import Session
from backend.models.utilisateur import Utilisateur
from backend.core.security import verify_password, create_access_token
from backend.schemas.auth_schema import TokenResponse

class AuthService:
    def __init__(self, db: Session):
        self.db = db

    def authenticate(self, identifiant: str, mot_de_passe: str):
        user = self.db.query(Utilisateur).filter(Utilisateur.identifiant == identifiant).first()
        if not user or not verify_password(mot_de_passe, user.mot_de_passe_hash):
            return None
        token = create_access_token({"sub": str(user.id), "role": user.role})
        return TokenResponse(access_token=token, token_type="bearer", user_id=user.id)

    def get_user_by_id(self, user_id: int):
        return self.db.query(Utilisateur).filter(Utilisateur.id == user_id).first()
