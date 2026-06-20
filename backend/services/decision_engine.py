import json
import os
from typing import Dict, Any

class DecisionEngine:
    """
    Moteur décisionnel pour le calcul de la hauteur maximale autorisée.
    """
    def __init__(self):
        self.config_path = "backend/data/decision_rules.json"
        self._ensure_config_exists()

    def _ensure_config_exists(self):
        """Crée un fichier de règles par défaut si celui-ci n'existe pas."""
        if not os.path.exists(self.config_path):
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            # Données de référence simulées : Hauteurs de base par aéroport et surface
            default_rules = {
                "aeroports": {
                    "Aéroport de Tunis-Carthage": {"base_height": 150, "factor": 1.1},
                    "Aéroport de Sfax": {"base_height": 130, "factor": 1.0},
                    "Aéroport de Bizerte": {"base_height": 120, "factor": 0.9},
                },
                "surfaces": {
                    "Piste": {"multiplier": 1.0},
                    "Approche": {"multiplier": 0.8},
                    "Transition": {"multiplier": 0.6},
                },
                "objets": {
                    "Éolienne": {"bonus": 20},
                    "Bâtiment": {"bonus": 10},
                    "Pylône": {"bonus": 5},
                    "GRU": {"bonus": 0},
                    "Station mobile": {"bonus": -5},
                },
                "global": {
                    "distance_factor": 0.01
                }
            }
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(default_rules, f, indent=4, ensure_ascii=False)

    def load_rules(self) -> Dict[str, Any]:
        with open(self.config_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def calculate_max_height(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calcule la hauteur max autorisée selon la règle :
        H_max = (Base_Aero * Facteur_Aero * Mult_Surface) + Bonus_Objet + (Distance * Facteur_Dist)
        """
        rules = self.load_rules()
        
        aeroport = data.get("aeroport")
        surface = data.get("surface")
        objet = data.get("objet")
        distance = data.get("distance", 0) or 0

        aero_data = rules["aeroports"].get(aeroport, {"base_height": 100, "factor": 1.0})
        surf_data = rules["surfaces"].get(surface, {"multiplier": 1.0})
        obj_data = rules["objets"].get(objet, {"bonus": 0})
        global_rules = rules.get("global", {"distance_factor": 0.01})

        # Règle mathématique
        base = aero_data["base_height"]
        factor = aero_data["factor"]
        mult = surf_data["multiplier"]
        bonus = obj_data["bonus"]
        dist_factor = global_rules.get("distance_factor", 0.01)

        max_authorized = (base * factor * mult) + bonus + (distance * dist_factor)
        
        # On simule aussi la hauteur demandée pour l'écart
        try:
            requested_height = float(data.get("altitude_finale", 160))
        except (ValueError, TypeError):
            requested_height = 160.0
            
        gap = max_authorized - requested_height

        return {
            "hauteur_max_autorisee": round(max_authorized, 2),
            "hauteur_demandee": round(requested_height, 2),
            "ecart": round(gap, 2),
            "status": "FAVORABLE" if gap >= 0 else "DÉFAVORABLE"
        }

decision_engine = DecisionEngine()