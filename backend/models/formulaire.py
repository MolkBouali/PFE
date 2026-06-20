"""
Modele ORM - Table formulaires_numerises.
Formulaire scanne uploade pour un dossier.
typeFormulaire detecte par ArUco : EOLIENNE | BATIMENT | GRU | PYLONE | AUTRE.
Relation 1-1 avec Dossier.
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.database.connection import Base

class FormulaireNumerise(Base):
    __tablename__ = "formulaires_numerises"
    id = Column(Integer, primary_key=True, index=True)
    dossier_id = Column(Integer, ForeignKey("dossiers.id"), unique=True)
    nom_fichier = Column(String, nullable=False)
    format = Column(String)
    type_formulaire = Column(String)
    nombre_pages = Column(Integer, default=1)
    marqueur_aruco = Column(Integer)
    chemin_stockage = Column(String)
    date_upload = Column(DateTime)
    dossier = relationship("Dossier", back_populates="formulaire")
    points_mesure = relationship("PointMesure", back_populates="formulaire")
