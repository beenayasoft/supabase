#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp_btp.settings')
django.setup()

from rest_framework.test import APIRequestFactory, force_authenticate
from devis.views import QuoteItemViewSet
from devis.models import Quote
from django.contrib.auth import get_user_model

User = get_user_model()

def debug_quote_item_viewset():
    print("🔍 Debugging QuoteItemViewSet...")
    
    try:
        # Récupérer un utilisateur et un devis
        user = User.objects.filter(email='admin@beenaya.com').first()
        quote = Quote.objects.first()
        
        if not user:
            print("❌ Utilisateur admin non trouvé")
            return
        if not quote:
            print("❌ Devis non trouvé")
            return
        
        print(f"✅ Utilisateur: {user.email}")
        print(f"✅ Devis: {quote.number}")
        
        # Créer une factory pour simuler une requête
        factory = APIRequestFactory()
        
        # Données pour créer un élément
        item_data = {
            "quote": str(quote.id),
            "type": "work",
            "position": 1,
            "designation": "Test ViewSet Élément",
            "description": "Description de test",
            "unit": "forfait",
            "quantity": 1,
            "unit_price": 1500.00,
            "discount": 0,
            "vat_rate": "20",
            "margin": 20
        }
        
        print(f"\\n🏗️ Test du ViewSet avec: {item_data}")
        
        # Créer une requête POST
        request = factory.post('/api/quote-items/', item_data, format='json')
        
        # Authentifier l'utilisateur
        force_authenticate(request, user=user)
        
        # Créer le viewset et exécuter l'action
        view = QuoteItemViewSet.as_view({'post': 'create'})
        
        print(f"✅ ViewSet créé, tentative de création...")
        
        response = view(request)
        
        print(f"✅ Réponse reçue: {response.status_code}")
        print(f"   Données: {response.data}")
        
    except Exception as e:
        print(f"❌ Erreur dans le viewset:")
        print(f"   Type: {type(e).__name__}")
        print(f"   Message: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    debug_quote_item_viewset() 