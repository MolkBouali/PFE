"""
Modele ORM - Table etudes_techniques.
Parametres DEA saisis par l agent + resultat du calcul de conformite.
Relation 1-1 avec Dossier.
"""
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.database.connection import Base

class EtudeTechnique(Base):
    __tablename__ = "etudes_techniques"
    id = Column(Integer, primary_key=True)
    dossier_id = Column(Integer, ForeignKey("dossiers.id"), unique=True)
    aeroport = Column(String)
    type_surface = Column(String)
    type_objet = Column(String)
    altitude_sol = Column(Float)
    altitude_finale = Column(Float)
    hauteur_demandee = Column(Float)
    distance_piste = Column(Float)
    hauteur_max_autorisee = Column(Float)
    ecart_calcule = Column(Float)
    conformite = Column(Boolean)
    date_enregistrement = Column(DateTime)
    dossier = relationship("Dossier", back_populates="etude_technique")
