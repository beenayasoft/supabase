#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp_btp.settings')
django.setup()

from devis.serializers import QuoteSerializer
from tiers.models import Tiers

def debug_quote_serializer():
    print("🔍 Debugging serializer de devis...")
    
    # Récupérer un client
    try:
        tier = Tiers.objects.first()
        if not tier:
            print("❌ Aucun tier trouvé")
            return
        
        print(f"✅ Tier trouvé: {tier.nom} (ID: {tier.id})")
        
        # Données pour le serializer
        quote_data = {
            "tier": tier.id,  # Utiliser l'ID comme dans l'API
            "project_name": "Test Serializer Projet",
            "project_address": "123 Rue Serializer",
            "validity_period": 30,
        }
        
        print(f"\n🏗️ Test du serializer avec: {quote_data}")
        
        # Créer le serializer
        serializer = QuoteSerializer(data=quote_data)
        
        print(f"✅ Serializer créé")
        
        # Valider les données
        if serializer.is_valid():
            print(f"✅ Données valides")
            
            # Sauvegarder
            try:
                quote = serializer.save()
                print(f"✅ Devis sauvegardé avec succès!")
                print(f"   - ID: {quote.id}")
                print(f"   - Numéro: {quote.number}")
                print(f"   - Client: {quote.client_name}")
                print(f"   - Statut: {quote.status}")
                
            except Exception as e:
                print(f"❌ Erreur lors de la sauvegarde:")
                print(f"   Type: {type(e).__name__}")
                print(f"   Message: {str(e)}")
                import traceback
                traceback.print_exc()
        else:
            print(f"❌ Données invalides: {serializer.errors}")
        
    except Exception as e:
        print(f"❌ Erreur générale:")
        print(f"   Type: {type(e).__name__}")
        print(f"   Message: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    debug_quote_serializer() 