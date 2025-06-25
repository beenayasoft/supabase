#!/usr/bin/env python3
"""
Script pour créer des données de test pour les devis.
Usage: python create_test_devis.py
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp_btp.settings')
django.setup()

from django.contrib.auth import get_user_model
from tiers.models import Tiers, Adresse, Contact
from devis.models import Quote, QuoteItem, QuoteStatus
from datetime import datetime, timedelta

User = get_user_model()

def create_test_data():
    """Créer des données de test pour les devis."""
    
    print("🚀 Création des données de test pour les devis...")
    
    # 1. Créer ou récupérer un utilisateur
    user, created = User.objects.get_or_create(
        email='admin@beenaya.com',
        defaults={
            'first_name': 'Admin',
            'last_name': 'Test',
            'is_staff': True,
            'is_superuser': True,
        }
    )
    if created:
        user.set_password('admin')
        user.save()
        print(f"✅ Utilisateur créé: {user.email}")
    else:
        print(f"✅ Utilisateur existant: {user.email}")
    
    # 2. Créer ou récupérer un client
    client, created = Tiers.objects.get_or_create(
        nom='Test Client SARL',
        defaults={
            'type': 'entreprise',
            'siret': '12345678901234',
            'tva': 'FR12345678901',
            'relation': 'client',
            'assigned_user': user,
        }
    )
    if created:
        print(f"✅ Client créé: {client.nom}")
        
        # Créer une adresse pour le client
        Adresse.objects.create(
            tier=client,
            libelle='Adresse principale',
            rue='123 Rue de Test',
            ville='Paris',
            code_postal='75001',
            pays='France',
            facturation=True
        )
        
        # Créer un contact pour le client
        Contact.objects.create(
            tier=client,
            nom='Dupont',
            prenom='Jean',
            fonction='Directeur',
            email='jean.dupont@testclient.com',
            telephone='0123456789',
            contact_principal_devis=True,
            contact_principal_facture=True
        )
    else:
        print(f"✅ Client existant: {client.nom}")
    
    # 3. Créer un devis de test
    quote, created = Quote.objects.get_or_create(
        number='DEV-TEST-001',
        defaults={
            'tier': client,
            'client_name': client.nom,
            'client_address': '123 Rue de Test, 75001 Paris',
            'project_name': 'Projet de Test',
            'project_address': '123 Rue de Test, 75001 Paris',
            'issue_date': datetime.now().date(),
            'validity_period': 30,
            'notes': 'Devis créé pour tester l\'API',
            'terms_and_conditions': 'Conditions générales de test',
            'status': QuoteStatus.DRAFT,
            'created_by': 'admin',
        }
    )
    if created:
        print(f"✅ Devis créé: {quote.number}")
        
        # Ajouter des éléments au devis
        items_data = [
            {
                'type': 'chapter',
                'position': 1,
                'designation': 'Travaux préparatoires',
                'quantity': 1,
                'unit_price': 0,
                'vat_rate': '20',
            },
            {
                'type': 'work',
                'position': 2,
                'designation': 'Préparation du chantier',
                'description': 'Installation et sécurisation de la zone de travail',
                'unit': 'forfait',
                'quantity': 1,
                'unit_price': 500,
                'vat_rate': '20',
                'margin': 15,
            },
            {
                'type': 'work',
                'position': 3,
                'designation': 'Peinture murs et plafonds',
                'description': 'Peinture acrylique blanche mate',
                'unit': 'm²',
                'quantity': 120,
                'unit_price': 25,
                'vat_rate': '20',
                'margin': 20,
            },
            {
                'type': 'product',
                'position': 4,
                'designation': 'Fournitures diverses',
                'description': 'Pinceaux, rouleaux, bâches',
                'unit': 'lot',
                'quantity': 1,
                'unit_price': 150,
                'vat_rate': '20',
                'discount': 10,
            },
        ]
        
        for item_data in items_data:
            QuoteItem.objects.create(quote=quote, **item_data)
        
        # Recalculer les totaux
        quote.update_totals()
        print(f"✅ {len(items_data)} éléments ajoutés au devis")
        print(f"   Total HT: {quote.total_ht} €")
        print(f"   Total TTC: {quote.total_ttc} €")
    else:
        print(f"✅ Devis existant: {quote.number}")
    
    # 4. Statistiques
    total_quotes = Quote.objects.count()
    total_clients = Tiers.objects.filter(relation='client').count()
    
    print(f"\n📊 STATISTIQUES:")
    print(f"   Clients: {total_clients}")
    print(f"   Devis: {total_quotes}")
    
    print(f"\n🎯 DONNÉES DE TEST CRÉÉES AVEC SUCCÈS!")
    print(f"   Email: admin@beenaya.com")
    print(f"   Mot de passe: admin")
    print(f"   Client: {client.nom} (ID: {client.id})")
    print(f"   Devis: {quote.number} (ID: {quote.id})")

if __name__ == "__main__":
    create_test_data() 