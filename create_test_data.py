#!/usr/bin/env python
"""
Script pour créer des données de test pour la bibliothèque d'ouvrages
"""

import os
import sys
import django

# Configuration de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp_btp.settings')
django.setup()

from bibliotheque.models import Categorie, Fourniture, MainOeuvre, Ouvrage, IngredientOuvrage
from django.contrib.contenttypes.models import ContentType

def create_test_data():
    print("Création des données de test pour la bibliothèque...")
    
    # 1. Créer des catégories
    print("Création des catégories...")
    
    # Catégories principales
    cat_materiaux = Categorie.objects.get_or_create(
        nom="Matériaux",
        defaults={'parent': None}
    )[0]
    
    cat_main_oeuvre = Categorie.objects.get_or_create(
        nom="Main d'œuvre",
        defaults={'parent': None}
    )[0]
    
    cat_ouvrages = Categorie.objects.get_or_create(
        nom="Ouvrages",
        defaults={'parent': None}
    )[0]
    
    # Sous-catégories matériaux
    cat_beton = Categorie.objects.get_or_create(
        nom="Béton",
        defaults={'parent': cat_materiaux}
    )[0]
    
    cat_acier = Categorie.objects.get_or_create(
        nom="Acier",
        defaults={'parent': cat_materiaux}
    )[0]
    
    cat_bois = Categorie.objects.get_or_create(
        nom="Bois",
        defaults={'parent': cat_materiaux}
    )[0]
    
    # Sous-catégories main d'œuvre
    cat_maconnerie = Categorie.objects.get_or_create(
        nom="Maçonnerie",
        defaults={'parent': cat_main_oeuvre}
    )[0]
    
    cat_charpente = Categorie.objects.get_or_create(
        nom="Charpente",
        defaults={'parent': cat_main_oeuvre}
    )[0]
    
    print(f"Créées {Categorie.objects.count()} catégories")
    
    # 2. Créer des fournitures (matériaux)
    print("Création des fournitures...")
    
    fournitures_data = [
        {
            'nom': 'Béton C25/30',
            'unite': 'm³',
            'prix_achat_ht': 85.00,
            'vat_rate': 20.0,
            'description': 'Béton dosé à 350 kg/m³',
            'reference': 'BET-C25-30',
            'supplier': 'Lafarge',
            'categorie': cat_beton,
            'type': 'material',
            'code': 'MAT001'
        },
        {
            'nom': 'Acier HA 10',
            'unite': 'kg',
            'prix_achat_ht': 1.20,
            'vat_rate': 20.0,
            'description': 'Acier haute adhérence diamètre 10mm',
            'reference': 'ACR-HA-10',
            'supplier': 'ArcelorMittal',
            'categorie': cat_acier,
            'type': 'material',
            'code': 'MAT002'
        },
        {
            'nom': 'Poutre bois 200x50',
            'unite': 'ml',
            'prix_achat_ht': 8.50,
            'vat_rate': 10.0,
            'description': 'Poutre en sapin du Nord 200x50mm',
            'reference': 'BOI-200-50',
            'supplier': 'Scierie Martin',
            'categorie': cat_bois,
            'type': 'material',
            'code': 'MAT003'
        },
        {
            'nom': 'Ciment Portland',
            'unite': 'T',
            'prix_achat_ht': 120.00,
            'vat_rate': 20.0,
            'description': 'Ciment Portland CEM I 52.5',
            'reference': 'CIM-PORT-52',
            'supplier': 'Lafarge',
            'categorie': cat_beton,
            'type': 'material',
            'code': 'MAT004'
        },
        {
            'nom': 'Gravier 10/20',
            'unite': 'T',
            'prix_achat_ht': 25.00,
            'vat_rate': 20.0,
            'description': 'Gravier concassé granulométrie 10/20',
            'reference': 'GRA-10-20',
            'supplier': 'Carrière Durand',
            'categorie': cat_beton,
            'type': 'material',
            'code': 'MAT005'
        }
    ]
    
    for data in fournitures_data:
        fourniture, created = Fourniture.objects.get_or_create(
            nom=data['nom'],
            defaults=data
        )
        if created:
            print(f"  - Créée: {fourniture.nom}")
    
    print(f"Total fournitures: {Fourniture.objects.count()}")
    
    # 3. Créer de la main d'œuvre
    print("Création de la main d'œuvre...")
    
    main_oeuvre_data = [
        {
            'nom': 'Maçon qualifié',
            'cout_horaire': 25.00,
            'unite': 'h',
            'description': 'Maçon avec 5+ ans d\'expérience',
            'categorie': cat_maconnerie,
            'type': 'labor',
            'code': 'LAB001'
        },
        {
            'nom': 'Aide maçon',
            'cout_horaire': 18.00,
            'unite': 'h',
            'description': 'Ouvrier spécialisé en maçonnerie',
            'categorie': cat_maconnerie,
            'type': 'labor',
            'code': 'LAB002'
        },
        {
            'nom': 'Charpentier',
            'cout_horaire': 28.00,
            'unite': 'h',
            'description': 'Charpentier traditionnel qualifié',
            'categorie': cat_charpente,
            'type': 'labor',
            'code': 'LAB003'
        },
        {
            'nom': 'Manœuvre',
            'cout_horaire': 15.00,
            'unite': 'h',
            'description': 'Manœuvre polyvalent',
            'categorie': cat_main_oeuvre,
            'type': 'labor',
            'code': 'LAB004'
        }
    ]
    
    for data in main_oeuvre_data:
        main_oeuvre, created = MainOeuvre.objects.get_or_create(
            nom=data['nom'],
            defaults=data
        )
        if created:
            print(f"  - Créée: {main_oeuvre.nom}")
    
    print(f"Total main d'œuvre: {MainOeuvre.objects.count()}")
    
    # 4. Créer des ouvrages
    print("Création des ouvrages...")
    
    ouvrages_data = [
        {
            'nom': 'Fondation béton armé',
            'unite': 'm³',
            'description': 'Fondation en béton armé avec ferraillage standard',
            'code': 'OUV001',
            'categorie': cat_ouvrages,
            'prix_recommande': 150.00,
            'marge': 25.0,
            'is_custom': False,
            'type': 'work',
            'complexity': 'medium',
            'efficiency': 1.0
        },
        {
            'nom': 'Mur béton banché',
            'unite': 'm²',
            'description': 'Mur en béton banché épaisseur 20cm',
            'code': 'OUV002',
            'categorie': cat_ouvrages,
            'prix_recommande': 85.00,
            'marge': 20.0,
            'is_custom': False,
            'type': 'work',
            'complexity': 'medium',
            'efficiency': 1.0
        },
        {
            'nom': 'Charpente traditionnelle',
            'unite': 'm²',
            'description': 'Charpente en bois traditionnelle',
            'code': 'OUV003',
            'categorie': cat_ouvrages,
            'prix_recommande': 120.00,
            'marge': 30.0,
            'is_custom': False,
            'type': 'work',
            'complexity': 'high',
            'efficiency': 0.8
        }
    ]
    
    for data in ouvrages_data:
        ouvrage, created = Ouvrage.objects.get_or_create(
            nom=data['nom'],
            defaults=data
        )
        if created:
            print(f"  - Créé: {ouvrage.nom}")
    
    print(f"Total ouvrages: {Ouvrage.objects.count()}")
    
    # 5. Créer des ingrédients pour les ouvrages
    print("Création des ingrédients d'ouvrages...")
    
    # Récupérer les objets créés
    fondation = Ouvrage.objects.get(nom='Fondation béton armé')
    beton = Fourniture.objects.get(nom='Béton C25/30')
    acier = Fourniture.objects.get(nom='Acier HA 10')
    macon = MainOeuvre.objects.get(nom='Maçon qualifié')
    aide = MainOeuvre.objects.get(nom='Aide maçon')
    
    # Content types
    fourniture_ct = ContentType.objects.get_for_model(Fourniture)
    main_oeuvre_ct = ContentType.objects.get_for_model(MainOeuvre)
    
    # Ingrédients pour fondation béton armé
    ingredients_fondation = [
        {
            'ouvrage': fondation,
            'element_type': fourniture_ct,
            'element_id': beton.id,
            'quantite': 1.0  # 1 m³ de béton pour 1 m³ de fondation
        },
        {
            'ouvrage': fondation,
            'element_type': fourniture_ct,
            'element_id': acier.id,
            'quantite': 80.0  # 80 kg d'acier pour 1 m³ de fondation
        },
        {
            'ouvrage': fondation,
            'element_type': main_oeuvre_ct,
            'element_id': macon.id,
            'quantite': 3.0  # 3 heures de maçon pour 1 m³
        },
        {
            'ouvrage': fondation,
            'element_type': main_oeuvre_ct,
            'element_id': aide.id,
            'quantite': 2.0  # 2 heures d'aide pour 1 m³
        }
    ]
    
    for data in ingredients_fondation:
        ingredient, created = IngredientOuvrage.objects.get_or_create(
            ouvrage=data['ouvrage'],
            element_type=data['element_type'],
            element_id=data['element_id'],
            defaults={'quantite': data['quantite']}
        )
        if created:
            print(f"  - Créé ingrédient: {ingredient}")
    
    print(f"Total ingrédients: {IngredientOuvrage.objects.count()}")
    
    print("\n=== RÉSUMÉ DES DONNÉES CRÉÉES ===")
    print(f"Catégories: {Categorie.objects.count()}")
    print(f"Fournitures: {Fourniture.objects.count()}")
    print(f"Main d'œuvre: {MainOeuvre.objects.count()}")
    print(f"Ouvrages: {Ouvrage.objects.count()}")
    print(f"Ingrédients: {IngredientOuvrage.objects.count()}")
    print("\nDonnées de test créées avec succès!")

if __name__ == '__main__':
    create_test_data() 