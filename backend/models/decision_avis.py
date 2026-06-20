"""
Modele ORM - Table decisions_avis.
Decision finale + validations des 4 directions (DER, DTA, DANA, DNA).
typeAvis : FAVORABLE | FAVORABLE_AVEC_BALISAGE | DEFAVORABLE.
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from backend.database.connection import Base

class DecisionAvis(Base):
    __tablename__ = "decisions_avis"
    id = Column(Integer, primary_key=True)
    dossier_id = Column(Integer, ForeignKey("dossiers.id"), unique=True)
    type_avis = Column(String)
    validation_der = Column(Boolean, default=False)
    validation_dta = Column(Boolean, default=False)
    validation_dana = Column(Boolean, default=False)
    validation_dna = Column(Boolean, default=False)
    justification = Column(Text)
    date_generation = Column(DateTime)
    numero_avis = Column(String, unique=True)
    agent_emetteur_id = Column(Integer, ForeignKey("utilisateurs.id"))
    dossier = relationship("Dossier", back_populates="decision_avis")
