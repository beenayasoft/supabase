#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json

# Configuration
API_URL = 'http://localhost:8000/api'

def test_create_quote():
    print("🔐 Authentification...")
    
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
            
            # Récupérer le premier client
            print('\n📋 Récupération d\'un client...')
            response = requests.get(f'{API_URL}/tiers/tiers/', headers=headers)
            if response.status_code == 200:
                clients = response.json()
                if clients:
                    client_id = clients[0]['id']
                    print(f'✅ Client trouvé: {clients[0]["nom"]} (ID: {client_id})')
                    
                    # Créer un devis
                    print('\n📋 Création d\'un devis...')
                    quote_data = {
                        "tier": client_id,
                        "project_name": "Test Projet API Simple",
                        "project_address": "123 Rue Test",
                        "validity_period": 30,
                    }
                    
                    response = requests.post(f'{API_URL}/quotes/', json=quote_data, headers=headers)
                    print(f'Status Code: {response.status_code}')
                    print(f'Response Headers: {dict(response.headers)}')
                    
                    if response.status_code == 201:
                        quote = response.json()
                        print(f'✅ Devis créé: {quote["number"]}')
                        return quote['id']
                    else:
                        print(f'❌ Erreur création devis: {response.status_code}')
                        print(f'Content-Type: {response.headers.get("content-type")}')
                        try:
                            print(f'Response JSON: {response.json()}')
                        except:
                            print(f'Response Text: {response.text[:500]}')
                        return None
                else:
                    print('❌ Aucun client trouvé')
                    return None
            else:
                print(f'❌ Erreur récupération clients: {response.status_code}')
                return None
                
        else:
            print(f'❌ Erreur authentification: {response.status_code}')
            return None
            
    except requests.exceptions.ConnectionError:
        print('❌ Erreur de connexion. Le serveur Django est-il démarré ?')
        return None
    except Exception as e:
        print(f'❌ Erreur inattendue: {e}')
        return None

if __name__ == '__main__':
    test_create_quote() 