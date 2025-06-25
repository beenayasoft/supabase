#!/usr/bin/env python3
"""
Script pour vérifier et corriger l'utilisateur admin.
"""

import os
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp_btp.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

print("👤 Vérification de l'utilisateur admin...")

try:
    user = User.objects.get(email='admin@beenaya.com')
    print(f"✅ Utilisateur trouvé: {user.email}")
    print(f"   ID: {user.id}")
    print(f"   Nom: {user.first_name} {user.last_name}")
    print(f"   Staff: {user.is_staff}")
    print(f"   Superuser: {user.is_superuser}")
    print(f"   Actif: {user.is_active}")
    print(f"   Date création: {user.date_joined}")
    
    # S'assurer que l'utilisateur est actif
    if not user.is_active:
        user.is_active = True
        user.save()
        print("✅ Utilisateur activé")
    
    # Remettre le mot de passe
    user.set_password('admin')
    user.save()
    print("✅ Mot de passe réinitialisé")
    
    # Vérifier l'authentification
    from django.contrib.auth import authenticate
    auth_user = authenticate(email='admin@beenaya.com', password='admin')
    if auth_user:
        print("✅ Authentification réussie")
    else:
        print("❌ Échec de l'authentification")
        
except User.DoesNotExist:
    print("❌ Utilisateur non trouvé, création...")
    user = User.objects.create_user(
        email='admin@beenaya.com',
        password='admin',
        first_name='Admin',
        last_name='Test',
        is_staff=True,
        is_superuser=True,
        is_active=True
    )
    print(f"✅ Utilisateur créé: {user.email}")

print("\n🔍 Liste de tous les utilisateurs:")
for u in User.objects.all():
    print(f"   {u.email} (actif: {u.is_active})") 