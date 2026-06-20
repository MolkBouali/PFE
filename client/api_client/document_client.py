"""Appels API generation documents."""
from client.api_client.http_client import HTTPClient

class DocumentClient(HTTPClient):
    def generate_pdf(self, dossier_id: int, data: dict):
        return self.post(f"/documents/generate/pdf/{dossier_id}", json=data)
    def generate_kmz(self, dossier_id: int):
        return self.post(f"/documents/generate/kmz/{dossier_id}")
