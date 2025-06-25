#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json

# Configuration
API_URL = 'http://localhost:8000/api'

def test_quote_item_creation():
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
            
            # Récupérer le premier devis
            print('\n�� Récupération d\'un devis...')
            response = requests.get(f'{API_URL}/quotes/', headers=headers)
            if response.status_code == 200:
                quotes_data = response.json()
                if isinstance(quotes_data, dict) and 'results' in quotes_data:
                    quotes = quotes_data['results']
                else:
                    quotes = quotes_data
                
                if quotes:
                    quote_id = quotes[0]['id']
                    print(f'✅ Devis trouvé: {quotes[0]["number"]} (ID: {quote_id})')
                    
                    # Créer un élément
                    print('\n🏗️ Création d\'un élément...')
                    item_data = {
                        "quote": quote_id,
                        "type": "work",
                        "position": 1,
                        "designation": "Test Debug Élément",
                        "description": "Description de test",
                        "unit": "forfait",
                        "quantity": 1,
                        "unit_price": 1500.00,
                        "discount": 0,
                        "vat_rate": "20",
                        "margin": 20
                    }
                    
                    print(f'Données: {json.dumps(item_data, indent=2)}')
                    
                    response = requests.post(f'{API_URL}/quote-items/', json=item_data, headers=headers)
                    print(f'Status Code: {response.status_code}')
                    print(f'Response Headers: {dict(response.headers)}')
                    
                    if response.status_code == 201:
                        item = response.json()
                        print(f'✅ Élément créé: {item["designation"]}')
                        print(f'   Total HT: {item["total_ht"]} €')
                        print(f'   Total TTC: {item["total_ttc"]} €')
                    else:
                        print(f'❌ Erreur création élément: {response.status_code}')
                        print(f'Response: {response.text[:1000]}...')
                
                else:
                    print('❌ Aucun devis trouvé')
            else:
                print(f'❌ Erreur récupération devis: {response.status_code}')
                print(response.text)
        else:
            print(f'❌ Erreur authentification: {response.status_code}')
            print(response.text)
            
    except Exception as e:
        print(f'❌ Erreur générale: {e}')
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_quote_item_creation() 