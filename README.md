# Système OACA — Gestion des demandes d'avis aéronautiques

Application client-serveur locale pour la dématérialisation et l'automatisation
du traitement des demandes d'avis d'obstacles aéronautiques (OACA).

## Stack technique
- Backend  : FastAPI (Python)
- Frontend : PySide6
- Base de données : PostgreSQL
- Modules IA : OpenCV ArUco + PaddleOCR

## Installation
```bash
pip install -r requirements.txt
```

## Lancement backend
```bash
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## Lancement client
```bash
cd client
python main.py
```
