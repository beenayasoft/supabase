#!/usr/bin/env python
"""
Script de débogage pour vérifier l'état des ContentTypes dans la base de données.
Exécutez-le avec : python debug_contenttypes.py
"""
import os
import sys
import django

# Configurer l'environnement Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp_btp.settings')
django.setup()

from django.contrib.contenttypes.models import ContentType
from bibliotheque.models import Categorie, Fourniture, MainOeuvre, Ouvrage, IngredientOuvrage

def debug_contenttypes():
    """Affiche des informations sur les ContentTypes disponibles."""
    print("\n=== DÉBOGAGE DES CONTENTTYPES ===\n")
    
    # Vérifier tous les ContentTypes
    all_content_types = ContentType.objects.all()
    print(f"Nombre total de ContentTypes: {all_content_types.count()}")
    
    # Afficher tous les ContentTypes
    print("\nListe de tous les ContentTypes:")
    for ct in all_content_types:
        print(f"- {ct.app_label}.{ct.model} (ID: {ct.id})")
    
    # Vérifier spécifiquement les ContentTypes dont nous avons besoin
    print("\nVérification des ContentTypes spécifiques:")
    
    # Fourniture
    try:
        fourniture_ct = ContentType.objects.get(model='fourniture')
        print(f"✓ ContentType 'fourniture' trouvé: {fourniture_ct.app_label}.{fourniture_ct.model} (ID: {fourniture_ct.id})")
    except ContentType.DoesNotExist:
        print("✗ ContentType 'fourniture' NON TROUVÉ")
    
    # MainOeuvre
    try:
        mainoeuvre_ct = ContentType.objects.get(model='mainoeuvre')
        print(f"✓ ContentType 'mainoeuvre' trouvé: {mainoeuvre_ct.app_label}.{mainoeuvre_ct.model} (ID: {mainoeuvre_ct.id})")
    except ContentType.DoesNotExist:
        print("✗ ContentType 'mainoeuvre' NON TROUVÉ")
    
    # Vérifier les modèles
    print("\nVérification des modèles dans la base de données:")
    print(f"- Nombre de Categorie: {Categorie.objects.count()}")
    print(f"- Nombre de Fourniture: {Fourniture.objects.count()}")
    print(f"- Nombre de MainOeuvre: {MainOeuvre.objects.count()}")
    print(f"- Nombre de Ouvrage: {Ouvrage.objects.count()}")
    print(f"- Nombre de IngredientOuvrage: {IngredientOuvrage.objects.count()}")
    
    # Afficher quelques exemples de données
    if Fourniture.objects.exists():
        print("\nExemples de Fournitures:")
        for f in Fourniture.objects.all()[:5]:  # Limité aux 5 premiers
            print(f"- ID: {f.id}, Nom: {f.nom}, Prix: {f.prix_achat_ht}€")
    
    if MainOeuvre.objects.exists():
        print("\nExemples de MainOeuvre:")
        for mo in MainOeuvre.objects.all()[:5]:  # Limité aux 5 premiers
            print(f"- ID: {mo.id}, Nom: {mo.nom}, Coût horaire: {mo.cout_horaire}€/h")

if __name__ == "__main__":
    debug_contenttypes() 