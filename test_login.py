import requests

url = "http://localhost:8000/auth/login"
payload = {
    "identifiant": "admin",
    "mot_de_passe": "admin123"
}

try:
    response = requests.post(url, json=payload)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")