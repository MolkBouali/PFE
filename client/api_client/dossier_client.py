"""Appels API dossiers."""
from client.api_client.http_client import HTTPClient

class DossierClient(HTTPClient):
    def get_all(self, params=None): return self.get("/dossiers/", params=params)
    def get_by_id(self, id): return self.get(f"/dossiers/{id}")
    def create_dossier(self, data): return self.post("/dossiers/", json=data)
    def update_dossier(self, id, data): return self.put(f"/dossiers/{id}", json=data)
    def re_extract(self, id, file): return self.post(f"/extract/{id}", files=file)
