"""
Modele ORM - Table documents_generes.
Tous les fichiers generes associes a un dossier.
Types : AVIS_PDF | KMZ | COMPLEMENT.
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, BigInteger
from sqlalchemy.orm import relationship
from backend.database.connection import Base

class DocumentGenere(Base):
    __tablename__ = "documents_generes"
    id = Column(Integer, primary_key=True)
    dossier_id = Column(Integer, ForeignKey("dossiers.id"))
    nom_fichier = Column(String)
    type_document = Column(String)
    chemin_stockage = Column(String)
    date_creation = Column(DateTime)
    taille = Column(BigInteger)
    dossier = relationship("Dossier", back_populates="documents_generes")
