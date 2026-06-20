"""Schemas Pydantic authentification."""
from pydantic import BaseModel

class LoginRequest(BaseModel):
    identifiant: str
    mot_de_passe: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user_id: int
