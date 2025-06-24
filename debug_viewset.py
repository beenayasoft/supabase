#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp_btp.settings')
django.setup()

from rest_framework.test import APIRequestFactory, force_authenticate
from devis.views import QuoteViewSet
from tiers.models import Tiers
from django.contrib.auth import get_user_model

User = get_user_model()

def debug_quote_viewset():
    print("🔍 Debugging QuoteViewSet...")
    
    try:
        # Récupérer un utilisateur et un tier
        user = User.objects.filter(email='admin@beenaya.com').first()
        tier = Tiers.objects.first()
        
        if not user:
            print("❌ Utilisateur admin non trouvé")
            return
        if not tier:
            print("❌ Tier non trouvé")
            return
        
        print(f"✅ Utilisateur: {user.email}")
        print(f"✅ Tier: {tier.nom}")
        
        # Créer une factory pour simuler une requête
        factory = APIRequestFactory()
        
        # Données pour créer un devis
        quote_data = {
            "tier": str(tier.id),
            "project_name": "Test ViewSet Projet",
            "project_address": "123 Rue ViewSet",
            "validity_period": 30,
        }
        
        print(f"\n🏗️ Test du ViewSet avec: {quote_data}")
        
        # Créer une requête POST
        request = factory.post('/api/quotes/', quote_data, format='json')
        
        # Authentifier l'utilisateur
        force_authenticate(request, user=user)
        
        # Créer le viewset et exécuter l'action
        view = QuoteViewSet.as_view({'post': 'create'})
        
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
    debug_quote_viewset() 