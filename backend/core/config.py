"""
Configuration globale de l application.
Lit les variables d environnement depuis le fichier .env.
Centralise : base de donnees, securite JWT, chemins de stockage.
"""
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/oaca_db"
    SECRET_KEY: str = "changeme-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    STORAGE_PATH: str = "./archives"
    TEMPLATES_PATH: str = "./templates"
    MODELS_IA_PATH: str = "./models_ia"
    class Config:
        env_file = ".env"

settings = Settings()
