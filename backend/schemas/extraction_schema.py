"""Schemas Pydantic extraction OCR."""
from pydantic import BaseModel
from typing import List, Any, Dict, Optional


class CoordonneesDTO(BaseModel):
    latitude_dms: str
    longitude_dms: str
    latitude_dd: Optional[float] = None
    longitude_dd: Optional[float] = None
    latitude_valide: bool = False
    longitude_valide: bool = False
    format_detecte: str = "Inconnu"


class DonneePointDTO(BaseModel):
    numero_ligne: int
    numero: Optional[str] = None
    coordonnees: CoordonneesDTO
    # Tous les autres champs extraits (spécifiques au marqueur ArUco détecté)
    donnees_specifiques: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class CoordonneesValidationDTO(BaseModel):
    """Validation DMS minimal (sans les champs de validation, qui sont calculés)."""
    latitude_dms: str
    longitude_dms: str


class PointValidationInput(BaseModel):
    """Un point à valider par le serveur."""
    numero_ligne: int
    numero: Optional[str] = None
    coordonnees: CoordonneesValidationDTO
    donnees_specifiques: Optional[Dict[str, Any]] = None


class ValidationRequest(BaseModel):
    points: List[PointValidationInput]


class ValidationResult(BaseModel):
    status: str = "ok"
    resultats: List[DonneePointDTO] = []
    statut_global: str = "succes"  # "succes", "succes_partiel", "echec"
    nb_valides: int = 0
    nb_total: int = 0


class StatistiquesDTO(BaseModel):
    total_lignes: int = 0
    lignes_valides: int = 0
    coordonnees_valides: int = 0
    taux_reussite: float = 0.0


class ExtractionResult(BaseModel):
    statut_extraction: str = "succes"  # "succes", "succes_partiel", "echec"
    taux_succes: float = 100.0
    message: str = ""
    donnees: List[DonneePointDTO] = []
    statistiques: StatistiquesDTO = StatistiquesDTO()
    formulaire_id: Optional[int] = None
    type_formulaire: Optional[str] = None
    format_detecte: str = "Inconnu"


class ConfirmationRequest(BaseModel):
    """Requête pour confirmer l'extraction et générer le KMZ."""
    formulaire_id: int
    points: List[PointValidationInput]