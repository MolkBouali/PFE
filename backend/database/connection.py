"""
Configuration connexion PostgreSQL.
Cree l engine SQLAlchemy, la session factory et la classe Base
utilisee par tous les modeles ORM.
La chaine de connexion est lue depuis DATABASE_URL dans .env.
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from backend.core.config import settings

engine = create_engine(settings.DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
