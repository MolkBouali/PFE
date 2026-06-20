"""Appels API statistiques."""
from client.api_client.http_client import HTTPClient

class StatsClient(HTTPClient):
    def get_stats(self, periode=None, region=None):
        params = {}
        if periode: params["periode"] = periode
        if region:  params["region"] = region
        return self.get("/stats/", params=params)
