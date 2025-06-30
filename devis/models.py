from django.db import models
import uuid
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from tiers.models import Tiers
from opportunite.models import Opportunity

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
            from decimal import Decimal, InvalidOperation
            
            # ✅ CONVERSION SÉCURISÉE DES TYPES POUR ÉVITER LES CONFLITS
            # Assurer que tous les champs numériques sont des Decimal
            try:
                unit_price = Decimal(str(self.unit_price)) if self.unit_price else Decimal('0')
                quantity = Decimal(str(self.quantity)) if self.quantity else Decimal('1')
                discount = Decimal(str(self.discount)) if self.discount else Decimal('0')
                vat_rate_value = Decimal(str(self.vat_rate)) if self.vat_rate else Decimal('20')
                
                # ✅ CALCULS AVEC TYPES DECIMAL UNIFORMES
                discount_factor = Decimal('1') - (discount / Decimal('100'))
                net_price = unit_price * discount_factor
                self.total_ht = net_price * quantity
                
                vat_rate_decimal = vat_rate_value / Decimal('100')
                vat_amount = self.total_ht * vat_rate_decimal
                self.total_ttc = self.total_ht + vat_amount
                
                print(f"💰 Calcul QuoteItem: {self.designation}")
                print(f"   unit_price={unit_price}, quantity={quantity}, discount={discount}%")
                print(f"   net_price={net_price}, total_ht={self.total_ht}, total_ttc={self.total_ttc}")
                
            except (ValueError, TypeError, InvalidOperation) as e:
                print(f"⚠️ Erreur de calcul QuoteItem {self.designation}: {e}")
                # Fallback avec valeurs par défaut
                self.total_ht = Decimal('0')
                self.total_ttc = Decimal('0')
        
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
    opportunity = models.ForeignKey(
        Opportunity, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name="quotes",
        verbose_name=_("Opportunité")
    )
    
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
        
        # Mettre à jour l'opportunité si elle existe
        if self.opportunity:
            from opportunite.models import OpportunityStatus
            
            # Si l'opportunité est en phase d'analyse des besoins ou nouvelle, la passer en négociation
            if self.opportunity.stage in [OpportunityStatus.NEEDS_ANALYSIS, OpportunityStatus.NEW]:
                self.opportunity.stage = OpportunityStatus.NEGOTIATION
                self.opportunity.save()
                print(f"✅ Opportunité {self.opportunity.id} mise à jour: {self.opportunity.stage}")
            else:
                print(f"ℹ️ Opportunité {self.opportunity.id} non mise à jour car déjà en phase {self.opportunity.stage}")
    
    def mark_as_accepted(self):
        """Marquer le devis comme accepté et mettre à jour l'opportunité associée"""
        self.status = QuoteStatus.ACCEPTED
        self.save()
        
        # Mettre à jour l'opportunité si elle existe
        if self.opportunity:
            from opportunite.models import OpportunityStatus
            
            # Si l'opportunité est en phase de négociation ou d'analyse, la marquer comme gagnée
            if self.opportunity.stage in [OpportunityStatus.NEGOTIATION, OpportunityStatus.NEEDS_ANALYSIS]:
                self.opportunity.stage = OpportunityStatus.WON
                self.opportunity.save()
                print(f"🎉 Opportunité {self.opportunity.id} marquée comme gagnée")
            elif self.opportunity.stage != OpportunityStatus.WON:
                print(f"⚠️ Opportunité {self.opportunity.id} non mise à jour car en phase {self.opportunity.stage}")
    
    def mark_as_rejected(self):
        """Marquer le devis comme refusé et mettre à jour l'opportunité associée si nécessaire"""
        self.status = QuoteStatus.REJECTED
        self.save()
        
        # Mettre à jour l'opportunité si elle existe et n'est pas déjà perdue ou gagnée
        if self.opportunity:
            from opportunite.models import OpportunityStatus
            
            # Si l'opportunité est en phase de négociation ou d'analyse, on peut la marquer comme perdue
            # seulement si c'est le seul devis associé à cette opportunité
            if self.opportunity.stage in [OpportunityStatus.NEGOTIATION, OpportunityStatus.NEEDS_ANALYSIS]:
                # Vérifier s'il y a d'autres devis actifs pour cette opportunité
                other_active_quotes = Quote.objects.filter(
                    opportunity=self.opportunity,
                    status__in=[QuoteStatus.DRAFT, QuoteStatus.SENT]
                ).exclude(id=self.id).exists()
                
                if not other_active_quotes:
                    # Si c'est le seul devis, on peut marquer l'opportunité comme perdue
                    self.opportunity.stage = OpportunityStatus.LOST
                    self.opportunity.loss_reason = "no_decision"  # Raison par défaut
                    self.opportunity.loss_description = "Devis refusé par le client"
                    self.opportunity.save()
                    print(f"❌ Opportunité {self.opportunity.id} marquée comme perdue suite au refus du devis")
                else:
                    print(f"ℹ️ Opportunité {self.opportunity.id} non mise à jour car d'autres devis sont en cours")
            else:
                print(f"ℹ️ Opportunité {self.opportunity.id} non mise à jour car déjà en phase {self.opportunity.stage}")
    
    def mark_as_expired(self):
        """Marquer le devis comme expiré"""
        self.status = QuoteStatus.EXPIRED
        self.save()
    
    def mark_as_cancelled(self):
        """Marquer le devis comme annulé"""
        self.status = QuoteStatus.CANCELLED
        self.save() 