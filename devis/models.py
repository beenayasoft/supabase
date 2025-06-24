from django.db import models
import uuid
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from tiers.models import Tiers
# from opportunite.models import Opportunity  # Temporairement commenté pour les migrations

def get_current_date():
    """Retourne la date courante (pas datetime)."""
    return timezone.now().date()

class QuoteStatus(models.TextChoices):
    DRAFT = "draft", _("Brouillon")
    SENT = "sent", _("Envoyé")
    ACCEPTED = "accepted", _("Accepté")
    REJECTED = "rejected", _("Refusé")
    EXPIRED = "expired", _("Expiré")
    CANCELLED = "cancelled", _("Annulé")

class VATRate(models.TextChoices):
    ZERO = "0", _("0%")
    REDUCED = "5.5", _("5.5%")
    INTERMEDIATE = "10", _("10%")
    STANDARD = "20", _("20%")

class QuoteItem(models.Model):
    PRODUCT = "product"
    SERVICE = "service"
    WORK = "work"
    CHAPTER = "chapter"
    SECTION = "section"
    DISCOUNT = "discount"
    
    TYPE_CHOICES = [
        (PRODUCT, _("Produit")),
        (SERVICE, _("Service")),
        (WORK, _("Ouvrage")),
        (CHAPTER, _("Chapitre")),
        (SECTION, _("Section")),
        (DISCOUNT, _("Remise")),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    quote = models.ForeignKey(
        "Quote", 
        on_delete=models.CASCADE, 
        related_name="items",
        verbose_name=_("Devis")
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
    margin = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name=_("Marge (%)"))
    total_ht = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name=_("Total HT"))
    total_ttc = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name=_("Total TTC"))
    
    # Pour les ouvrages
    work_id = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("ID Ouvrage"))
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Élément de devis")
        verbose_name_plural = _("Éléments de devis")
        ordering = ["position"]
    
    def __str__(self):
        return f"{self.designation} - {self.total_ht} €"
    
    def save(self, *args, **kwargs):
        # Calculer le total HT et TTC
        if self.type not in ["chapter", "section"]:
            from decimal import Decimal
            net_price = self.unit_price * (1 - self.discount / 100)
            self.total_ht = net_price * self.quantity
            vat_rate_decimal = Decimal(str(self.vat_rate)) / 100
            vat_amount = self.total_ht * vat_rate_decimal
            self.total_ttc = self.total_ht + vat_amount
        
        super().save(*args, **kwargs)
        
        # Mettre à jour les totaux du devis parent
        if self.quote:
            self.quote.update_totals()

class Quote(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    number = models.CharField(max_length=50, unique=True, verbose_name=_("Numéro"))
    status = models.CharField(
        max_length=20,
        choices=QuoteStatus.choices,
        default=QuoteStatus.DRAFT,
        verbose_name=_("Statut")
    )
    
    # Relations avec les autres modèles
    tier = models.ForeignKey(
        Tiers, 
        on_delete=models.CASCADE, 
        related_name="quotes",
        verbose_name=_("Client")
    )
    # opportunity = models.ForeignKey(
    #     Opportunity, 
    #     on_delete=models.SET_NULL, 
    #     null=True, 
    #     blank=True,
    #     related_name="quotes",
    #     verbose_name=_("Opportunité")
    # )
    
    # Informations client et projet
    client_name = models.CharField(max_length=255, verbose_name=_("Nom du client"))
    client_address = models.TextField(blank=True, null=True, verbose_name=_("Adresse du client"))
    project_name = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("Nom du projet"))
    project_address = models.TextField(blank=True, null=True, verbose_name=_("Adresse du projet"))
    
    # Dates
    issue_date = models.DateField(default=get_current_date, verbose_name=_("Date d'émission"))
    expiry_date = models.DateField(null=True, blank=True, verbose_name=_("Date d'expiration"))
    validity_period = models.PositiveIntegerField(default=30, verbose_name=_("Durée de validité (jours)"))
    
    # Contenu
    notes = models.TextField(blank=True, null=True, verbose_name=_("Notes"))
    terms_and_conditions = models.TextField(blank=True, null=True, verbose_name=_("Conditions générales"))
    
    # Montants calculés
    total_ht = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name=_("Total HT"))
    total_vat = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name=_("Total TVA"))
    total_ttc = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name=_("Total TTC"))
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Créé le"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Mis à jour le"))
    created_by = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("Créé par"))
    updated_by = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("Mis à jour par"))
    
    class Meta:
        verbose_name = _("Devis")
        verbose_name_plural = _("Devis")
        ordering = ["-created_at"]
    
    def __str__(self):
        return f"{self.number} - {self.client_name} - {self.total_ttc} €"
    
    def save(self, *args, **kwargs):
        # Générer le numéro automatiquement s'il n'est pas défini
        if not self.number:
            from django.db.models import Max
            import datetime
            
            current_year = datetime.datetime.now().year
            last_quote = Quote.objects.filter(
                number__startswith=f'DEV-{current_year}'
            ).aggregate(Max('number'))
            
            if last_quote['number__max']:
                # Extraire le dernier numéro et incrémenter
                last_number = int(last_quote['number__max'].split('-')[-1])
                self.number = f'DEV-{current_year}-{last_number + 1:03d}'
            else:
                # Premier devis de l'année
                self.number = f'DEV-{current_year}-001'
        
        # Remplir les informations client si non définies
        if not self.client_name and self.tier:
            self.client_name = self.tier.nom
            
            # Récupérer l'adresse principale de facturation ou la première adresse
            if not self.client_address:
                billing_address = self.tier.adresses.filter(facturation=True).first()
                if billing_address:
                    self.client_address = f"{billing_address.rue}, {billing_address.code_postal} {billing_address.ville}"
                elif self.tier.adresses.exists():
                    first_address = self.tier.adresses.first()
                    self.client_address = f"{first_address.rue}, {first_address.code_postal} {first_address.ville}"
        
        # Calculer la date d'expiration si non définie
        if self.issue_date and not self.expiry_date and self.validity_period:
            self.expiry_date = self.issue_date + timezone.timedelta(days=self.validity_period)
        
        super().save(*args, **kwargs)
    
    def update_totals(self):
        """Mettre à jour les totaux du devis"""
        items = self.items.exclude(type__in=["chapter", "section"])
        self.total_ht = sum(item.total_ht for item in items)
        self.total_vat = sum(item.total_ttc - item.total_ht for item in items)
        self.total_ttc = self.total_ht + self.total_vat
        self.save()
    
    def mark_as_sent(self):
        """Marquer le devis comme envoyé et mettre à jour l'opportunité associée"""
        self.status = QuoteStatus.SENT
        self.save()
        
        # Mettre à jour l'opportunité si elle existe et est en phase d'analyse des besoins
        # if self.opportunity and self.opportunity.stage == "needs_analysis":
        #     self.opportunity.stage = "negotiation"
        #     self.opportunity.save()
    
    def mark_as_accepted(self):
        """Marquer le devis comme accepté et mettre à jour l'opportunité associée"""
        self.status = QuoteStatus.ACCEPTED
        self.save()
        
        # Mettre à jour l'opportunité si elle existe et est en phase de négociation
        # if self.opportunity and self.opportunity.stage == "negotiation":
        #     self.opportunity.stage = "won"
        #     self.opportunity.save()
    
    def mark_as_rejected(self):
        """Marquer le devis comme refusé"""
        self.status = QuoteStatus.REJECTED
        self.save()
    
    def mark_as_expired(self):
        """Marquer le devis comme expiré"""
        self.status = QuoteStatus.EXPIRED
        self.save()
    
    def mark_as_cancelled(self):
        """Marquer le devis comme annulé"""
        self.status = QuoteStatus.CANCELLED
        self.save() 