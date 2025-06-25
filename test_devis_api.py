#!/usr/bin/env python3
"""
Script de test pour l'API des devis.
Usage: python test_devis_api.py
"""

import requests
import json
from datetime import datetime, timedelta

# Configuration
BASE_URL = "http://localhost:8000/api"
USERNAME = "admin"  # À adapter selon votre utilisateur
PASSWORD = "admin"  # À adapter selon votre mot de passe

class DevisAPITester:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.client_id = None
        self.quote_id = None
    
    def authenticate(self):
        """S'authentifier et obtenir un token JWT."""
        try:
            response = self.session.post(f"{BASE_URL}/auth/login/", {
                "email": "admin@beenaya.com",
                "password": PASSWORD
            })
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get('access')
                self.session.headers.update({
                    'Authorization': f'Bearer {self.token}'
                })
                print("✅ Authentification réussie")
                return True
            else:
                print(f"❌ Erreur d'authentification: {response.status_code}")
                print(response.text)
                return False
        except Exception as e:
            print(f"❌ Erreur lors de l'authentification: {e}")
            return False
    
    def test_quotes_stats(self):
        """Tester l'endpoint des statistiques."""
        try:
            response = self.session.get(f"{BASE_URL}/quotes/stats/")
            
            if response.status_code == 200:
                stats = response.json()
                print("✅ Statistiques des devis récupérées:")
                print(f"   Total: {stats.get('total', 0)}")
                print(f"   Brouillons: {stats.get('draft', 0)}")
                print(f"   Envoyés: {stats.get('sent', 0)}")
                print(f"   Acceptés: {stats.get('accepted', 0)}")
                print(f"   Montant total: {stats.get('total_amount', 0)} €")
                return True
            else:
                print(f"❌ Erreur lors de la récupération des stats: {response.status_code}")
                print(response.text)
                return False
        except Exception as e:
            print(f"❌ Erreur lors du test des stats: {e}")
            return False
    
    def get_first_client(self):
        """Récupérer le premier client disponible."""
        try:
            response = self.session.get(f"{BASE_URL}/tiers/tiers/")
            
            if response.status_code == 200:
                clients = response.json()
                if isinstance(clients, dict) and 'results' in clients:
                    clients = clients['results']
                
                if clients and len(clients) > 0:
                    self.client_id = clients[0]['id']
                    print(f"✅ Client trouvé: {clients[0]['nom']} (ID: {self.client_id})")
                    return True
                else:
                    print("❌ Aucun client trouvé")
                    return False
            else:
                print(f"❌ Erreur lors de la récupération des clients: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Erreur lors de la récupération du client: {e}")
            return False
    
    def test_create_quote(self):
        """Tester la création d'un devis."""
        if not self.client_id:
            print("❌ Pas de client disponible pour créer un devis")
            return False
        
        try:
            quote_data = {
                "tier": self.client_id,
                "project_name": "Test Projet API",
                "project_address": "123 Rue de Test, 75001 Paris",
                "validity_period": 30,
                "notes": "Devis créé via test API",
                "terms_and_conditions": "Conditions générales de test"
            }
            
            response = self.session.post(f"{BASE_URL}/quotes/", json=quote_data)
            
            if response.status_code == 201:
                quote = response.json()
                self.quote_id = quote['id']
                print(f"✅ Devis créé avec succès:")
                print(f"   ID: {quote['id']}")
                print(f"   Numéro: {quote['number']}")
                print(f"   Client: {quote['client_name']}")
                print(f"   Statut: {quote['status_display']}")
                return True
            else:
                print(f"❌ Erreur lors de la création du devis: {response.status_code}")
                print(response.text)
                return False
        except Exception as e:
            print(f"❌ Erreur lors de la création du devis: {e}")
            return False
    
    def test_add_quote_item(self):
        """Tester l'ajout d'un élément au devis."""
        if not self.quote_id:
            print("❌ Pas de devis disponible pour ajouter un élément")
            return False
        
        try:
            item_data = {
                "quote": self.quote_id,
                "type": "work",
                "position": 1,
                "designation": "Travaux de test",
                "description": "Description détaillée des travaux",
                "unit": "forfait",
                "quantity": 1,
                "unit_price": 1500.00,
                "discount": 0,
                "vat_rate": "20",
                "margin": 20
            }
            
            response = self.session.post(f"{BASE_URL}/quote-items/", json=item_data)
            
            if response.status_code == 201:
                item = response.json()
                print(f"✅ Élément ajouté au devis:")
                print(f"   ID: {item['id']}")
                print(f"   Désignation: {item['designation']}")
                print(f"   Total HT: {item['total_ht']} €")
                print(f"   Total TTC: {item['total_ttc']} €")
                return True
            else:
                print(f"❌ Erreur lors de l'ajout de l'élément: {response.status_code}")
                print(response.text)
                return False
        except Exception as e:
            print(f"❌ Erreur lors de l'ajout de l'élément: {e}")
            return False
    
    def test_get_quote_detail(self):
        """Tester la récupération du détail d'un devis."""
        if not self.quote_id:
            print("❌ Pas de devis disponible pour récupérer les détails")
            return False
        
        try:
            response = self.session.get(f"{BASE_URL}/quotes/{self.quote_id}/")
            
            if response.status_code == 200:
                quote = response.json()
                print(f"✅ Détails du devis récupérés:")
                print(f"   Numéro: {quote['number']}")
                print(f"   Total HT: {quote['total_ht']} €")
                print(f"   Total TTC: {quote['total_ttc']} €")
                print(f"   Nombre d'éléments: {len(quote.get('items', []))}")
                return True
            else:
                print(f"❌ Erreur lors de la récupération du devis: {response.status_code}")
                print(response.text)
                return False
        except Exception as e:
            print(f"❌ Erreur lors de la récupération du devis: {e}")
            return False
    
    def test_mark_as_sent(self):
        """Tester le marquage d'un devis comme envoyé."""
        if not self.quote_id:
            print("❌ Pas de devis disponible pour marquer comme envoyé")
            return False
        
        try:
            response = self.session.post(f"{BASE_URL}/quotes/{self.quote_id}/mark_as_sent/", json={
                "note": "Devis envoyé via test API"
            })
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Devis marqué comme envoyé:")
                print(f"   Message: {result['detail']}")
                return True
            else:
                print(f"❌ Erreur lors du marquage comme envoyé: {response.status_code}")
                print(response.text)
                return False
        except Exception as e:
            print(f"❌ Erreur lors du marquage comme envoyé: {e}")
            return False
    
    def test_list_quotes(self):
        """Tester la liste des devis avec filtres."""
        try:
            # Test sans filtre
            response = self.session.get(f"{BASE_URL}/quotes/")
            
            if response.status_code == 200:
                quotes = response.json()
                if isinstance(quotes, dict) and 'results' in quotes:
                    quotes = quotes['results']
                
                print(f"✅ Liste des devis récupérée ({len(quotes)} devis)")
                
                # Test avec filtre de statut
                response = self.session.get(f"{BASE_URL}/quotes/?status=sent")
                if response.status_code == 200:
                    sent_quotes = response.json()
                    if isinstance(sent_quotes, dict) and 'results' in sent_quotes:
                        sent_quotes = sent_quotes['results']
                    print(f"✅ Devis envoyés filtrés ({len(sent_quotes)} devis)")
                
                return True
            else:
                print(f"❌ Erreur lors de la récupération de la liste: {response.status_code}")
                print(response.text)
                return False
        except Exception as e:
            print(f"❌ Erreur lors du test de la liste: {e}")
            return False
    
    def run_all_tests(self):
        """Exécuter tous les tests."""
        print("🚀 Début des tests de l'API Devis")
        print("=" * 50)
        
        # Authentification
        if not self.authenticate():
            return False
        
        # Tests des endpoints
        tests = [
            ("Statistiques des devis", self.test_quotes_stats),
            ("Récupération du client", self.get_first_client),
            ("Création d'un devis", self.test_create_quote),
            ("Ajout d'un élément", self.test_add_quote_item),
            ("Détail du devis", self.test_get_quote_detail),
            ("Marquage comme envoyé", self.test_mark_as_sent),
            ("Liste des devis", self.test_list_quotes),
        ]
        
        results = []
        for test_name, test_func in tests:
            print(f"\n📋 Test: {test_name}")
            result = test_func()
            results.append((test_name, result))
        
        # Résumé
        print("\n" + "=" * 50)
        print("📊 RÉSUMÉ DES TESTS")
        print("=" * 50)
        
        passed = 0
        for test_name, result in results:
            status = "✅ PASSÉ" if result else "❌ ÉCHOUÉ"
            print(f"{status} - {test_name}")
            if result:
                passed += 1
        
        print(f"\n🎯 Résultat: {passed}/{len(results)} tests réussis")
        
        if self.quote_id:
            print(f"\n💡 ID du devis de test créé: {self.quote_id}")
            print("   Vous pouvez le consulter dans l'admin Django ou via l'API")
        
        return passed == len(results)


if __name__ == "__main__":
    tester = DevisAPITester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 Tous les tests sont passés ! L'API Devis est fonctionnelle.")
    else:
        print("\n⚠️  Certains tests ont échoué. Vérifiez la configuration.")
    
    exit(0 if success else 1) 