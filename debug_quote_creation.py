#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp_btp.settings')
django.setup()

from devis.models import Quote
from tiers.models import Tiers
from datetime import date

def debug_quote_creation():
    print("🔍 Debugging création de devis...")
    
    # Récupérer un client
    try:
        tier = Tiers.objects.first()
        if not tier:
            print("❌ Aucun tier trouvé")
            return
        
        print(f"✅ Tier trouvé: {tier.nom}")
        print(f"   - ID: {tier.id}")
        print(f"   - Type: {tier.type}")
        print(f"   - Relation: {tier.relation}")
        
        # Créer un devis manuellement
        quote_data = {
            'tier': tier,
            'project_name': 'Test Debug Projet',
            'project_address': '123 Rue Debug',
            'validity_period': 30,
        }
        
        print(f"\n🏗️ Création du devis avec les données: {quote_data}")
        
        # Essayer de créer le devis
        quote = Quote(**quote_data)
        quote.save()
        
        print(f"✅ Devis créé avec succès!")
        print(f"   - ID: {quote.id}")
        print(f"   - Numéro: {quote.number}")
        print(f"   - Client: {quote.client_name}")
        print(f"   - Statut: {quote.status}")
        
    except Exception as e:
        print(f"❌ Erreur lors de la création du devis:")
        print(f"   Type: {type(e).__name__}")
        print(f"   Message: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    debug_quote_creation() 