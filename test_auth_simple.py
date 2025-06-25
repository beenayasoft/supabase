#!/usr/bin/env python3
"""
Script simple pour tester l'authentification.
"""

import requests
import json

BASE_URL = "http://localhost:8000/api"

# Test d'authentification
auth_data = {
    "email": "admin@beenaya.com",
    "password": "admin"
}

print("🔐 Test d'authentification...")
print(f"URL: {BASE_URL}/auth/login/")
print(f"Données: {auth_data}")

try:
    response = requests.post(f"{BASE_URL}/auth/login/", json=auth_data)
    print(f"Status: {response.status_code}")
    print(f"Réponse: {response.text}")
    
    if response.status_code == 200:
        data = response.json()
        token = data.get('access')
        print(f"✅ Token obtenu: {token[:50]}...")
        
        # Tester l'API avec le token
        headers = {'Authorization': f'Bearer {token}'}
        
        print("\n📊 Test des statistiques devis...")
        stats_response = requests.get(f"{BASE_URL}/quotes/stats/", headers=headers)
        print(f"Status: {stats_response.status_code}")
        print(f"Réponse: {stats_response.text}")
        
        print("\n📋 Test de la liste des devis...")
        quotes_response = requests.get(f"{BASE_URL}/quotes/", headers=headers)
        print(f"Status: {quotes_response.status_code}")
        print(f"Réponse: {quotes_response.text}")
        
    else:
        print("❌ Échec de l'authentification")
        
except Exception as e:
    print(f"❌ Erreur: {e}") 