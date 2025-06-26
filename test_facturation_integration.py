#!/usr/bin/env python
"""
Script de test pour vérifier l'intégration du module de facturation
avec les modules tiers et devis.

Usage: python test_facturation_integration.py
"""

import os
import sys
import django
from decimal import Decimal

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp_btp.settings')
django.setup()

from django.test import TestCase
from django.utils import timezone
from tiers.models import Tiers, Adresse
from devis.models import Quote, QuoteItem
from facturation.models import Invoice, InvoiceItem, Payment


def test_integration():
    """Test complet d'intégration entre tiers, devis et facturation"""
    
    print("🧪 Démarrage des tests d'intégration facturation...")
    
    # 1. Créer un tier client
    print("\n1️⃣ Création d'un tier client...")
    tier = Tiers.objects.create(
        type=Tiers.TYPE_ENTREPRISE,
        nom="Dupont Construction SARL",
        siret="12345678901234",
        relation=Tiers.RELATION_CLIENT
    )
    
    adresse = Adresse.objects.create(
        tier=tier,
        libelle="Siège social",
        rue="123 Rue de la Construction",
        ville="Paris",
        code_postal="75001",
        facturation=True
    )
    
    print(f"✅ Tier créé: {tier.nom} (ID: {tier.id})")
    print(f"✅ Adresse créée: {adresse}")
    
    # 2. Créer un devis
    print("\n2️⃣ Création d'un devis...")
    quote = Quote.objects.create(
        tier=tier,
        project_name="Rénovation bureaux",
        project_address="456 Avenue des Affaires, 75002 Paris",
        validity_period=30,
        notes="Devis pour rénovation complète"
    )
    
    # Ajouter des éléments au devis
    QuoteItem.objects.create(
        quote=quote,
        type="work",
        designation="Travaux de plomberie",
        quantity=1,
        unit_price=Decimal('2500.00'),
        vat_rate="20"
    )
    
    QuoteItem.objects.create(
        quote=quote,
        type="work", 
        designation="Travaux d'électricité",
        quantity=1,
        unit_price=Decimal('1800.00'),
        vat_rate="20"
    )
    
    quote.update_totals()
    print(f"✅ Devis créé: {quote.number} - Total: {quote.total_ttc}€")
    
    # 3. Créer une facture depuis le devis
    print("\n3️⃣ Création d'une facture depuis le devis...")
    invoice = Invoice.objects.create(
        tier=tier,
        quote=quote,
        project_name="Rénovation bureaux - Phase 1",
        payment_terms=30,
        notes="Facture d'acompte 30%"
    )
    
    # Créer un élément d'acompte
    acompte_amount = quote.total_ht * Decimal('0.30')  # 30% d'acompte
    InvoiceItem.objects.create(
        invoice=invoice,
        type="advance_payment",
        designation=f"Acompte 30% - Devis N°{quote.number}",
        quantity=1,
        unit_price=acompte_amount,
        vat_rate="20"
    )
    
    invoice.update_totals()
    print(f"✅ Facture créée: {invoice.number} - Total: {invoice.total_ttc}€")
    
    # 4. Tester les propriétés calculées pour compatibilité frontend
    print("\n4️⃣ Test des propriétés de compatibilité frontend...")
    print(f"   client_id: {invoice.client_id}")
    print(f"   quote_id: {invoice.quote_id}")
    print(f"   project_id: {invoice.project_id}")
    print(f"   client_name: {invoice.client_name}")
    print(f"   client_address: {invoice.client_address}")
    
    # 5. Valider et émettre la facture
    print("\n5️⃣ Validation et émission de la facture...")
    invoice.validate_and_send()
    print(f"✅ Facture validée: {invoice.number} - Statut: {invoice.status}")
    
    # 6. Enregistrer un paiement
    print("\n6️⃣ Enregistrement d'un paiement...")
    payment = invoice.record_payment(
        amount=invoice.total_ttc,  # Paiement complet
        method="bank_transfer",
        reference="VIR-20250120-001",
        notes="Paiement acompte"
    )
    print(f"✅ Paiement enregistré: {payment.amount}€ - Statut facture: {invoice.status}")
    
    # 7. Créer une facture complète depuis le devis
    print("\n7️⃣ Création d'une facture totale depuis le devis...")
    invoice_total = Invoice.objects.create(
        tier=tier,
        quote=quote,
        project_name="Rénovation bureaux - Facture finale",
        payment_terms=30,
        notes="Facture totale moins acompte"
    )
    
    # Copier tous les éléments du devis
    for quote_item in quote.items.all():
        InvoiceItem.objects.create(
            invoice=invoice_total,
            type=quote_item.type,
            parent=quote_item.parent,
            position=quote_item.position,
            reference=quote_item.reference,
            designation=quote_item.designation,
            description=quote_item.description,
            unit=quote_item.unit,
            quantity=quote_item.quantity,
            unit_price=quote_item.unit_price,
            discount=quote_item.discount,
            vat_rate=quote_item.vat_rate,
            work_id=quote_item.work_id
        )
    
    # Ajouter une ligne de déduction pour l'acompte
    InvoiceItem.objects.create(
        invoice=invoice_total,
        type="advance_payment",
        designation=f"Déduction acompte facture N°{invoice.number}",
        quantity=1,
        unit_price=-acompte_amount,  # Montant négatif
        vat_rate="20"
    )
    
    invoice_total.update_totals()
    print(f"✅ Facture totale créée: {invoice_total.number} - Total: {invoice_total.total_ttc}€")
    
    # 8. Créer un avoir
    print("\n8️⃣ Création d'un avoir...")
    credit_note = invoice_total.create_credit_note(
        reason="Test de création d'avoir",
        is_full_credit_note=False,
        selected_items=[invoice_total.items.first().id]  # Avoir partiel
    )
    print(f"✅ Avoir créé: {credit_note.number} - Total: {credit_note.total_ttc}€")
    print(f"   Facture originale statut: {invoice_total.status}")
    
    # 9. Vérifications finales
    print("\n9️⃣ Vérifications finales...")
    print(f"   Tier {tier.nom}:")
    print(f"     - Nombre de factures: {tier.invoices.count()}")
    print(f"     - Nombre de devis: {tier.quotes.count()}")
    
    print(f"   Devis {quote.number}:")
    print(f"     - Nombre de factures liées: {quote.invoices.count()}")
    
    # Calcul des totaux
    total_invoiced = sum(inv.total_ttc for inv in tier.invoices.all())
    total_paid = sum(inv.paid_amount for inv in tier.invoices.all())
    
    print(f"   Totaux financiers:")
    print(f"     - Total facturé: {total_invoiced}€")
    print(f"     - Total payé: {total_paid}€")
    print(f"     - Restant dû: {total_invoiced - total_paid}€")
    
    print("\n✅ Tests d'intégration terminés avec succès!")
    return True


if __name__ == "__main__":
    try:
        test_integration()
    except Exception as e:
        print(f"\n❌ Erreur durant les tests: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1) 