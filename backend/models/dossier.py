"""
Modele ORM - Table dossiers.
Entite centrale du systeme. Represente une demande d avis aeronautique.
Statuts : en_cours | en_attente_complement | traite | archive.
"""
from sqlalchemy import Column, Integer, String, Date, ForeignKey, Text
from sqlalchemy.orm import relationship
from backend.database.connection import Base

class Dossier(Base):
    __tablename__ = "dossiers"
    id = Column(Integer, primary_key=True, index=True)
    numero_dossier = Column(String, unique=True, nullable=False, index=True)
    nom_demandeur = Column(String, nullable=False)
    identifiant_depositaire = Column(String, nullable=False)
    region = Column(String)
    type_demande = Column(String)
    statut = Column(String, default="en_cours")
    avis = Column(String, default="non_genere")
    complement = Column(String, default="aucun")
    observations = Column(Text)
    date_depot = Column(Date)
    date_traitement = Column(Date)
    agent_id = Column(Integer, ForeignKey("utilisateurs.id"))
    agent = relationship("Utilisateur")
    formulaire = relationship("FormulaireNumerise", back_populates="dossier", uselist=False)
    etude_technique = relationship("EtudeTechnique", back_populates="dossier", uselist=False)
    decision_avis = relationship("DecisionAvis", back_populates="dossier", uselist=False)
    documents_generes = relationship("DocumentGenere", back_populates="dossier")
