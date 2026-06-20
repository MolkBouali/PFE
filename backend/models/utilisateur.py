"""
Modele ORM - Table utilisateurs.
Agents instructeurs habilites a utiliser le systeme.
Colonnes : id, identifiant (unique), mot_de_passe_hash, nom, prenom, matricule, role, statut.
"""
from sqlalchemy import Column, Integer, String, Boolean
from backend.database.connection import Base

class Utilisateur(Base):
    __tablename__ = "utilisateurs"
    id = Column(Integer, primary_key=True, index=True)
    identifiant = Column(String, unique=True, nullable=False, index=True)
    mot_de_passe_hash = Column(String, nullable=False)
    nom = Column(String, nullable=False)
    prenom = Column(String, nullable=False)
    matricule = Column(String, unique=True)
    role = Column(String, default="agent")
    statut = Column(Boolean, default=True)
