"""Appels API moteur decisionnel."""
from client.api_client.http_client import HTTPClient

class DecisionClient(HTTPClient):
    def analyse(self, dossier_id: int, data: dict):
        return self.post(f"/decision/analyse/{dossier_id}", json=data)
