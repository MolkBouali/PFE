# Bibliothèques Utilisées dans le Projet

Ce document présente un résumé des bibliothèques et frameworks utilisés dans le cadre du développement du projet, classés par rôle et besoin technique.

| Catégorie | Bibliothèque | Rôle et Besoin |
| :--- | :--- | :--- |
| **Framework Web & API** | `fastapi` | Développement d'une API REST performante et typée. |
| | `uvicorn` | Serveur ASGI pour l'exécution de l'application FastAPI. |
| | `pydantic` | Validation des données et définition des schémas. |
| | `python-multipart` | Gestion des formulaires et téléchargement de fichiers via l'API. |
| **Base de Données & ORM** | `sqlalchemy` | Mapping objet-relationnel (ORM) pour la gestion de la BDD. |
| | `psycopg2-binary` | Adaptateur permettant la connexion à la base de données PostgreSQL. |
| | `alembic` | Gestion et versioning des migrations de la base de données. |
| **Sécurité & Authentification** | `python-jose` | Implémentation des jetons JWT pour l'authentification sécurisée. |
| | `passlib` | Hachage sécurisé des mots de passe (algorithme bcrypt). |
| **OCR & Traitement d'Image** | `paddleocr` | Extraction de texte à partir d'images et de documents (OCR). |
| | `paddlepaddle` | Framework de Deep Learning supportant PaddleOCR. |
| | `opencv-python` | Traitement et manipulation d'images pour optimiser l'OCR. |
| | `numpy` | Calculs numériques et manipulation des matrices d'images. |
| **Traitement de Documents** | `python-docx` | Analyse et extraction de données depuis des fichiers Microsoft Word. |
| | `simplekml` | Génération et manipulation de fichiers KML pour les données géospatiales. |
| **Interface Utilisateur (UI)** | `PySide6` | Développement de l'application cliente desktop via le framework Qt. |
| **Utilitaires & Infrastructure** | `requests` | Client HTTP pour la communication entre le client et le serveur. |
| | `docker` | Interaction avec l'API Docker pour la gestion des conteneurs. |