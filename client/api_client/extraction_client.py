"""Appels API extraction automatique."""
from client.api_client.http_client import HTTPClient

class ExtractionClient(HTTPClient):
    def extract(self, dossier_id: int, file_bytes: bytes, filename: str):
        """Upload le formulaire et lance le pipeline ArUco + OCR."""
        return self.post(f"/extraction/extract/{dossier_id}",
                         files={"file": (filename, file_bytes)})
