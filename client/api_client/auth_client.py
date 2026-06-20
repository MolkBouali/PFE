"""Appels API authentification."""
from client.api_client.http_client import HTTPClient

class AuthClient(HTTPClient):
    def __init__(self): super().__init__()
    def login(self, identifiant: str, mot_de_passe: str):
        return self.post("/auth/login", json={"identifiant": identifiant, "mot_de_passe": mot_de_passe})
