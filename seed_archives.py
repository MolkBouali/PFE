import sys
import os

# Add the root directory to sys.path to allow imports from backend
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.database.connection import SessionLocal
from backend.models.utilisateur import Utilisateur
from backend.models.dossier import Dossier
from backend.models.formulaire import FormulaireNumerise
from backend.models.etude_technique import EtudeTechnique
from backend.models.decision_avis import DecisionAvis
from backend.models.document_genere import DocumentGenere
from backend.models.point_mesure import PointMesure

# Mapping from visual values in JSON to backend internal keys
MAP_STATUTS = {"Traité": "traite", "En cours": "en_cours"}
MAP_AVIS = {
    "Favorable": "favorable", 
    "Favorable avec balisage": "favorable_balisage", 
    "Défavorable": "defavorable", 
    "--": "non_genere"
}
MAP_COMPLEMENT = {"Reçu": "recu", "En attente": "en_attente", "Traité": "traite", "--": "aucun"}

data = [
    {
        "numero_dossier": "DOS-2026-001",
        "nom_demandeur": "STEG Energies Renouvelables",
        "type_demande": "Eolienne",
        "region": "Tunis",
        "statut": MAP_STATUTS.get("Traité"),
        "avis": MAP_AVIS.get("Favorable"),
        "complement": MAP_COMPLEMENT.get("--"),
        "date_depot": "2026-01-15"
    },
    {
        "numero_dossier": "DOS-2026-002",
        "nom_demandeur": "SNCF Maroc",
        "type_demande": "Electrification",
        "region": "Casablanca",
        "statut": MAP_STATUTS.get("Traité"),
        "avis": MAP_AVIS.get("Favorable avec balisage"),
        "complement": MAP_COMPLEMENT.get("Reçu"),
        "date_depot": "2026-02-10"
    },
    {
        "numero_dossier": "DOS-2026-003",
        "nom_demandeur": "Air Algérie",
        "type_demande": "Extension Piste",
        "region": "Alger",
        "statut": MAP_STATUTS.get("En cours"),
        "avis": MAP_AVIS.get("--"),
        "complement": MAP_COMPLEMENT.get("En attente"),
        "date_depot": "2026-03-05"
    },
    {
        "numero_dossier": "DOS-2026-004",
        "nom_demandeur": "Port Autonome Dakar",
        "type_demande": "Sondage",
        "region": "Dakar",
        "statut": MAP_STATUTS.get("Traité"),
        "avis": MAP_AVIS.get("Défavorable"),
        "complement": MAP_COMPLEMENT.get("Traité"),
        "date_depot": "2026-03-22"
    },
    {
        "numero_dossier": "DOS-2026-005",
        "nom_demandeur": "Senelec",
        "type_demande": "Ligne Haute Tension",
        "region": "Thies",
        "statut": MAP_STATUTS.get("En cours"),
        "avis": MAP_AVIS.get("--"),
        "complement": MAP_COMPLEMENT.get("--"),
        "date_depot": "2026-04-01"
    }
]

def seed():
    db = SessionLocal()
    try:
        print("Seeding archives data...")
        for item in data:
            # Check if dossier already exists to avoid duplicates
            exists = db.query(Dossier).filter(Dossier.numero_dossier == item["numero_dossier"]).first()
            if exists:
                print(f"Dossier {item['numero_dossier']} already exists. Skipping.")
                continue
            
            dossier = Dossier(**item)
            db.add(dossier)
        
        db.commit()
        print("Seeding completed successfully!")
    except Exception as e:
        print(f"Error during seeding: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed()