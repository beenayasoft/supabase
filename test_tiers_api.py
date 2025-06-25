#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json

# Configuration
API_URL = 'http://localhost:8000/api'

def test_tiers_api():
    print("🔐 Test d'authentification...")
    
    # Authentification
    auth_data = {
        'email': 'admin@beenaya.com',
        'password': 'admin'
    }
    
    try:
        response = requests.post(f'{API_URL}/auth/login/', json=auth_data)
        if response.status_code == 200:
            token = response.json()['access']
            headers = {'Authorization': f'Bearer {token}'}
            print('✅ Authentification réussie')
            
            # Tester l'API des tiers
            print('\n📋 Test de l\'API des tiers...')
            response = requests.get(f'{API_URL}/tiers/tiers/', headers=headers)
            print(f'Status: {response.status_code}')
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    print(f'✅ Tiers récupérés: {len(data)} éléments')
                    for tier in data[:3]:  # Afficher les 3 premiers
                        print(f'  - ID: {tier.get("id")}, Nom: {tier.get("nom", "N/A")}')
                else:
                    print(f'✅ Réponse: {json.dumps(data, indent=2)}')
            else:
                print(f'❌ Erreur: {response.status_code} - {response.text}')
                
        else:
            print(f'❌ Erreur d\'authentification: {response.status_code} - {response.text}')
            
    except requests.exceptions.ConnectionError:
        print('❌ Erreur de connexion. Le serveur Django est-il démarré sur http://localhost:8000 ?')
    except Exception as e:
        print(f'❌ Erreur inattendue: {e}')

if __name__ == '__main__':
    test_tiers_api() 