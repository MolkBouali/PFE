"""
Client HTTP de base.
Gere la session requests, les headers Authorization Bearer et l URL de base.
Tous les clients specifiques heritent de cette classe.
"""
import requests
from typing import Optional, Any

BASE_URL = "http://localhost:8000"

class HTTPClient:
    def __init__(self, token: Optional[str] = None):
        self.session = requests.Session()
        self.base_url = BASE_URL
        if token:
            self.session.headers.update({"Authorization": f"Bearer {token}"})

    def get(self, path: str, params: dict = None) -> Optional[Any]:
        try:
            r = self.session.get(f"{self.base_url}{path}", params=params, timeout=30)
            r.raise_for_status()
            return r.json()
        except requests.RequestException:
            return None

    def post_binary(self, path: str, json: dict = None, files: dict = None) -> Optional[bytes]:
        """Envoie des données et récupère le contenu binaire de la réponse (ex: génération de PDF)."""
        try:
            r = self.session.post(f"{self.base_url}{path}", json=json, files=files, timeout=60)
            r.raise_for_status()
            return r.content
        except requests.RequestException:
            return None

    def post(self, path: str, json: dict = None, files: dict = None) -> Optional[Any]:
        try:
            r = self.session.post(f"{self.base_url}{path}", json=json, files=files, timeout=60)
            r.raise_for_status()
            return r.json()
        except requests.RequestException:
            return None

    def put(self, path: str, json: dict = None) -> Optional[Any]:
        try:
            r = self.session.put(f"{self.base_url}{path}", json=json, timeout=30)
            r.raise_for_status()
            return r.json()
        except requests.RequestException:
            return None

    def get_binary(self, path: str, params: dict = None) -> Optional[bytes]:
        """Récupère le contenu binaire d'une ressource (ex: fichier KMZ)."""
        try:
            r = self.session.get(f"{self.base_url}{path}", params=params, timeout=30)
            r.raise_for_status()
            return r.content
        except requests.RequestException:
            return None
