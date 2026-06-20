"""
Modele ORM - Table points_mesure.
Une ligne du formulaire = un obstacle individuel.
Ex : parc eolien de 9 eoliennes -> 9 PointMesure.
donnees_specifiques (JSON) : champs variables selon typeFormulaire
  ex. diametre_rotor pour EOLIENNE, hauteur_batiment pour BATIMENT.
"""
from sqlalchemy import Column, Integer, String, Boolean, JSON, ForeignKey
from sqlalchemy.orm import relationship
from backend.database.connection import Base

class PointMesure(Base):
    __tablename__ = "points_mesure"
    id = Column(Integer, primary_key=True, index=True)
    formulaire_id = Column(Integer, ForeignKey("formulaires_numerises.id"))
    numero_ligne = Column(Integer, nullable=False)
    coordinates = Column(JSON) # Stores {'lat': '...', 'lon': '...'}
    coordonnee_valide = Column(Boolean, default=False)
    corrigee_manuellement = Column(Boolean, default=False)
    donnees_specifiques = Column(JSON)
    page_source = Column(Integer, default=1)
    formulaire = relationship("FormulaireNumerise", back_populates="points_mesure")
