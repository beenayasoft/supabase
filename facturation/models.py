from django.db import models
import uuid
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from decimal import Decimal
from tiers.models import Tiers


def get_current_date():
    """Retourne la date courante (pas datetime)."""
    return timezone.now().date()


class InvoiceStatus(models.TextChoices):
    """Statuts possibles pour une facture - Compatible frontend InvoiceStatus"""
    DRAFT = "draft", _("Brouillon")
    SENT = "sent", _("Émise")
    OVERDUE = "overdue", _("En retard")
    PARTIALLY_PAID = "partially_paid", _("Payée partiellement")
    PAID = "paid", _("Payée")
    CANCELLED = "cancelled", _("Annulée")
    CANCELLED_BY_CREDIT_NOTE = "cancelled_by_credit_note", _("Annulée par avoir")


class VATRate(models.TextChoices):
    """Taux de TVA - Compatible frontend VATRate"""
    ZERO = "0", _("0%")
    REDUCED_7 = "7", _("7%")
    REDUCED_10 = "10", _("10%")
    INTERMEDIATE = "14", _("14%")
    STANDARD = "20", _("20%")


class PaymentMethod(models.TextChoices):
    """Méthodes de paiement - Compatible frontend PaymentMethod"""
    BANK_TRANSFER = "bank_transfer", _("Virement bancaire")
    CHECK = "check", _("Chèque")
    CASH = "cash", _("Espèces")
    CARD = "card", _("Carte bancaire")
    OTHER = "other", _("Autre")


class Invoice(models.Model):
    """
    Modèle de facture - Compatible avec l'interface frontend Invoice
    """
    # Identifiants
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    number = models.CharField(max_length=50, default="Brouillon", verbose_name=_("Numéro"))
    status = models.CharField(
        max_length=30,
        choices=InvoiceStatus.choices,
        default=InvoiceStatus.DRAFT,
        verbose_name=_("Statut")
    )
    is_credit_note = models.BooleanField(default=False, verbose_name=_("Est un avoir"))
    
    # Relations avec les autres modèles
    tier = models.ForeignKey(
        Tiers, 
        on_delete=models.CASCADE, 
        related_name="invoices",
        verbose_name=_("Client")
    )
    
    # Informations client (dénormalisées pour performance et compatibilité frontend)
    client_name = models.CharField(max_length=255, verbose_name=_("Nom du client"))
    client_address = models.TextField(blank=True, null=True, verbose_name=_("Adresse du client"))
    
    # Projet/Chantier (dénormalisé depuis le devis ou saisi manuellement)
    # En attente du module chantier - pour l'instant stockage libre
    # Ces champs sont automatiquement remplis depuis le devis lié si disponible
    project_name = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("Nom du projet/chantier"))
    project_address = models.TextField(blank=True, null=True, verbose_name=_("Adresse du projet/chantier"))
    project_reference = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("Référence projet"))
    
    # Dates
    issue_date = models.DateField(default=get_current_date, verbose_name=_("Date d'émission"))
    due_date = models.DateField(null=True, blank=True, verbose_name=_("Date d'échéance"))
    payment_terms = models.PositiveIntegerField(default=30, verbose_name=_("Délai de paiement (jours)"))
    
    # Contenu
    notes = models.TextField(blank=True, null=True, verbose_name=_("Notes"))
    terms_and_conditions = models.TextField(blank=True, null=True, verbose_name=_("Conditions générales"))
    
    # Montants calculés (compatible frontend)
    total_ht = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name=_("Total HT"))
    total_vat = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name=_("Total TVA"))
    total_ttc = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name=_("Total TTC"))
    paid_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name=_("Montant payé"))
    remaining_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name=_("Restant dû"))
    
    # Relations avec d'autres documents
    quote = models.ForeignKey(
        'devis.Quote',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="invoices",
        verbose_name=_("Devis d'origine")
    )
    quote_number = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("Numéro devis d'origine"))
    
    # Relations pour les avoirs
    credit_note = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="credit_notes_created",
        verbose_name=_("Avoir associé")
    )
    original_invoice = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="credit_notes",
        verbose_name=_("Facture d'origine (pour avoir)")
    )
    
    # Métadonnées (compatible frontend)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Créé le"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Mis à jour le"))
    created_by = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("Créé par"))
    updated_by = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("Mis à jour par"))
    
    class Meta:
        verbose_name = _("Facture")
        verbose_name_plural = _("Factures")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['tier']),
            models.Index(fields=['issue_date']),
            models.Index(fields=['due_date']),
            models.Index(fields=['quote']),
        ]
    
    def __str__(self):
        return f"{self.number} - {self.client_name} - {self.total_ttc} €"
    
    @property
    def client_id(self):
        """Propriété pour compatibilité frontend - retourne l'ID du tier"""
        return str(self.tier.id) if self.tier else None
    
    @property
    def project_id(self):
        """Propriété pour compatibilité frontend - retourne la référence projet"""
        return self.project_reference if self.project_reference else None
    
    @property
    def quote_id(self):
        """Propriété pour compatibilité frontend - retourne l'ID du devis"""
        return str(self.quote.id) if self.quote else None
    
    @property
    def credit_note_id(self):
        """Propriété pour compatibilité frontend - retourne l'ID de l'avoir"""
        return str(self.credit_note.id) if self.credit_note else None
    
    @property
    def original_invoice_id(self):
        """Propriété pour compatibilité frontend - retourne l'ID de la facture d'origine"""
        return str(self.original_invoice.id) if self.original_invoice else None
    
    def save(self, *args, **kwargs):
        # Remplir les informations client si non définies
        if not self.client_name and self.tier:
            self.client_name = self.tier.nom
            
            # Récupérer l'adresse principale de facturation
            if not self.client_address:
                billing_address = self.tier.adresses.filter(facturation=True).first()
                if billing_address:
                    self.client_address = f"{billing_address.rue}, {billing_address.code_postal} {billing_address.ville}"
                elif self.tier.adresses.exists():
                    first_address = self.tier.adresses.first()
                    self.client_address = f"{first_address.rue}, {first_address.code_postal} {first_address.ville}"
        
        # Remplir les informations du devis si lié
        if self.quote:
            # Toujours synchroniser le numéro de devis
            if not self.quote_number:
                self.quote_number = self.quote.number
            
            # Récupérer automatiquement les infos projet du devis si pas déjà définies
            if not self.project_name and self.quote.project_name:
                self.project_name = self.quote.project_name
            if not self.project_address and self.quote.project_address:
                self.project_address = self.quote.project_address
            
            # Si le client n'est pas défini, le prendre du devis
            if not self.client_name and self.quote.client_name:
                self.client_name = self.quote.client_name
            if not self.client_address and self.quote.client_address:
                self.client_address = self.quote.client_address
        
        # Calculer la date d'échéance si non définie
        if self.issue_date and not self.due_date and self.payment_terms:
            from datetime import timedelta
            self.due_date = self.issue_date + timedelta(days=self.payment_terms)
        
        # Calculer remaining_amount
        self.remaining_amount = self.total_ttc - self.paid_amount
        
        super().save(*args, **kwargs)
    
    def update_totals(self):
        """Mettre à jour les totaux de la facture"""
        items = self.items.exclude(type__in=["chapter", "section"])
        self.total_ht = sum(item.total_ht for item in items)
        self.total_vat = sum(item.total_ttc - item.total_ht for item in items)
        self.total_ttc = self.total_ht + self.total_vat
        self.remaining_amount = self.total_ttc - self.paid_amount
        self.save()
    
    def validate_and_send(self):
        """User Story 5.3: Valider et émettre une facture"""
        if self.status != InvoiceStatus.DRAFT:
            raise ValueError("Seules les factures brouillon peuvent être validées")
        
        # Générer un numéro définitif si c'est encore "Brouillon"
        if self.number == "Brouillon":
            from django.db.models import Max
            import datetime
            
            current_year = datetime.datetime.now().year
            last_invoice = Invoice.objects.filter(
                number__startswith=f'FAC-{current_year}'
            ).aggregate(Max('number'))
            
            if last_invoice['number__max']:
                # Extraire le dernier numéro et incrémenter
                last_number = int(last_invoice['number__max'].split('-')[-1])
                self.number = f'FAC-{current_year}-{last_number + 1:03d}'
            else:
                # Première facture de l'année
                self.number = f'FAC-{current_year}-001'
        
        self.status = InvoiceStatus.SENT
        self.save()
    
    def record_payment(self, amount, method, date=None, reference=None, notes=None):
        """User Story 5.4: Enregistrer un règlement"""
        if self.status not in [InvoiceStatus.SENT, InvoiceStatus.PARTIALLY_PAID, InvoiceStatus.OVERDUE]:
            raise ValueError("Les paiements ne peuvent être enregistrés que sur des factures émises")
        
        if amount <= 0:
            raise ValueError("Le montant doit être positif")
        
        if amount > self.remaining_amount:
            raise ValueError("Le montant ne peut pas dépasser le restant dû")
        
        # Créer le paiement
        payment = Payment.objects.create(
            invoice=self,
            amount=amount,
            method=method,
            date=date or timezone.now().date(),
            reference=reference,
            notes=notes
        )
        
        # Mettre à jour les montants
        self.paid_amount += amount
        self.remaining_amount = self.total_ttc - self.paid_amount
        
        # Mettre à jour le statut
        if self.remaining_amount <= 0:
            self.status = InvoiceStatus.PAID
        elif self.paid_amount > 0 and self.remaining_amount > 0:
            self.status = InvoiceStatus.PARTIALLY_PAID
        
        self.save()
        return payment
    
    def create_credit_note(self, reason="", is_full_credit_note=True, selected_items=None):
        """User Story 5.5: Créer un avoir"""
        if self.status != InvoiceStatus.SENT:
            raise ValueError("Les avoirs ne peuvent être créés que pour des factures émises")
        
        # Créer l'avoir
        credit_note = Invoice.objects.create(
            tier=self.tier,
            client_id=self.client_id,
            client_name=self.client_name,
            client_address=self.client_address,
            project_id=self.project_id,
            project_name=self.project_name,
            project_address=self.project_address,
            issue_date=timezone.now().date(),
            payment_terms=self.payment_terms,
            notes=reason or f"Avoir pour la facture N°{self.number}",
            terms_and_conditions=self.terms_and_conditions,
            original_invoice_id=str(self.id),
            status=InvoiceStatus.DRAFT,
            is_credit_note=True
        )
        
        # Copier les éléments avec montants négatifs
        if is_full_credit_note:
            # Avoir total
            for item in self.items.all():
                InvoiceItem.objects.create(
                    invoice=credit_note,
                    type=item.type,
                    parent_id=item.parent_id,
                    position=item.position,
                    reference=item.reference,
                    designation=item.designation,
                    description=item.description,
                    unit=item.unit,
                    quantity=item.quantity,
                    unit_price=-item.unit_price,
                    discount=item.discount,
                    vat_rate=item.vat_rate,
                    total_ht=-item.total_ht,
                    total_ttc=-item.total_ttc,
                    work_id=item.work_id
                )
        else:
            # Avoir partiel
            if selected_items:
                items_to_credit = self.items.filter(id__in=selected_items)
                for item in items_to_credit:
                    InvoiceItem.objects.create(
                        invoice=credit_note,
                        type=item.type,
                        parent_id=item.parent_id,
                        position=item.position,
                        reference=item.reference,
                        designation=item.designation,
                        description=item.description,
                        unit=item.unit,
                        quantity=item.quantity,
                        unit_price=-item.unit_price,
                        discount=item.discount,
                        vat_rate=item.vat_rate,
                        total_ht=-item.total_ht,
                        total_ttc=-item.total_ttc,
                        work_id=item.work_id
                    )
        
        # Mettre à jour les totaux de l'avoir
        credit_note.update_totals()
        
        # Marquer la facture originale comme annulée et lier l'avoir
        self.status = InvoiceStatus.CANCELLED_BY_CREDIT_NOTE
        self.credit_note = credit_note
        self.save()
        
        # Lier l'avoir à la facture originale
        credit_note.original_invoice = self
        credit_note.save()
        
        return credit_note


class InvoiceItem(models.Model):
    """
    Modèle d'élément de facture - Compatible avec l'interface frontend InvoiceItem
    """
    # Types d'éléments (compatible frontend)
    PRODUCT = "product"
    SERVICE = "service"
    WORK = "work"
    CHAPTER = "chapter"
    SECTION = "section"
    DISCOUNT = "discount"
    ADVANCE_PAYMENT = "advance_payment"
    
    TYPE_CHOICES = [
        (PRODUCT, _("Produit")),
        (SERVICE, _("Service")),
        (WORK, _("Ouvrage")),
        (CHAPTER, _("Chapitre")),
        (SECTION, _("Section")),
        (DISCOUNT, _("Remise")),
        (ADVANCE_PAYMENT, _("Acompte")),
    ]
    
    # Champs compatibles frontend
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice = models.ForeignKey(
        Invoice, 
        on_delete=models.CASCADE, 
        related_name="items",
        verbose_name=_("Facture")
    )
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=PRODUCT)
    parent = models.ForeignKey(
        "self", 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name="children",
        verbose_name=_("Parent")
    )
    position = models.PositiveIntegerField(default=0, verbose_name=_("Position"))
    reference = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("Référence"))
    designation = models.CharField(max_length=255, verbose_name=_("Désignation"))
    description = models.TextField(blank=True, null=True, verbose_name=_("Description"))
    unit = models.CharField(max_length=20, blank=True, null=True, verbose_name=_("Unité"))
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1, verbose_name=_("Quantité"))
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name=_("Prix unitaire"))
    discount = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name=_("Remise (%)"))
    vat_rate = models.CharField(
        max_length=10, 
        choices=VATRate.choices, 
        default=VATRate.STANDARD,
        verbose_name=_("Taux TVA")
    )
    total_ht = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name=_("Total HT"))
    total_ttc = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name=_("Total TTC"))
    work_id = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("ID Ouvrage"))
    
    class Meta:
        verbose_name = _("Élément de facture")
        verbose_name_plural = _("Éléments de facture")
        ordering = ["position"]
    
    def __str__(self):
        return f"{self.designation} - {self.total_ht} €"
    
    @property
    def parent_id(self):
        """Propriété pour compatibilité frontend - retourne l'ID du parent"""
        return str(self.parent.id) if self.parent else None
    
    def save(self, *args, **kwargs):
        # Calculer les totaux si ce n'est pas un chapitre ou une section
        if self.type not in ["chapter", "section"]:
            try:
                unit_price = Decimal(str(self.unit_price)) if self.unit_price else Decimal('0')
                quantity = Decimal(str(self.quantity)) if self.quantity else Decimal('1')
                discount = Decimal(str(self.discount)) if self.discount else Decimal('0')
                vat_rate_value = Decimal(str(self.vat_rate)) if self.vat_rate else Decimal('20')
                
                # Calculs
                discount_factor = Decimal('1') - (discount / Decimal('100'))
                net_price = unit_price * discount_factor
                self.total_ht = net_price * quantity
                
                vat_rate_decimal = vat_rate_value / Decimal('100')
                vat_amount = self.total_ht * vat_rate_decimal
                self.total_ttc = self.total_ht + vat_amount
                
            except (ValueError, TypeError) as e:
                # Fallback avec valeurs par défaut
                self.total_ht = Decimal('0')
                self.total_ttc = Decimal('0')
        
        super().save(*args, **kwargs)
        
        # Mettre à jour les totaux de la facture parent
        if self.invoice:
            self.invoice.update_totals()


class Payment(models.Model):
    """
    Modèle de paiement - Compatible avec l'interface frontend Payment
    """
    # Champs compatibles frontend
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice = models.ForeignKey(
        Invoice, 
        on_delete=models.CASCADE, 
        related_name="payments",
        verbose_name=_("Facture")
    )
    date = models.DateField(default=get_current_date, verbose_name=_("Date du paiement"))
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name=_("Montant"))
    method = models.CharField(
        max_length=20,
        choices=PaymentMethod.choices,
        default=PaymentMethod.BANK_TRANSFER,
        verbose_name=_("Méthode de paiement")
    )
    reference = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("Référence"))
    notes = models.TextField(blank=True, null=True, verbose_name=_("Notes"))
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Créé le"))
    
    class Meta:
        verbose_name = _("Paiement")
        verbose_name_plural = _("Paiements")
        ordering = ["-date", "-created_at"]
    
    def __str__(self):
        return f"Paiement {self.amount} € - {self.invoice.number}"
