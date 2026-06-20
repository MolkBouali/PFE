"""
Point d'entrée FastAPI.
Enregistre tous les routers et configure les middlewares.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.database.connection import engine, Base
from backend.core.config import settings
from backend.api import auth, dossiers, extraction, decision, pdf_service, kmz_service, archives, statistiques

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Système OACA",
    description="API de gestion pour le système OACA, permettant l'extraction de données via IA, la gestion de dossiers, et l'analyse de documents KMZ et PDF.",
    version="1.0.0",
    doc_url="/docs",
    redoc_url="/redocs"
)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])

app.include_router(auth.router,          prefix="/auth",       tags=["Authentification"])
app.include_router(dossiers.router,      prefix="/dossiers",   tags=["Dossiers"])
app.include_router(extraction.router,    prefix="/extraction", tags=["Extraction IA"])
app.include_router(decision.router,      prefix="/decision",   tags=["Moteur décisionnel"])
app.include_router(pdf_service.router,   prefix="/documents",  tags=["Documents"])
app.include_router(kmz_service.router,   prefix="/documents",  tags=["Documents"])
app.include_router(archives.router,      prefix="/archives",   tags=["Archives"])
app.include_router(statistiques.router,  prefix="/stats",      tags=["Statistiques"])
