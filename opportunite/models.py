import uuid
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from tiers.models import Tiers

class OpportunityStatus(models.TextChoices):
    NEW = "new", _("Nouvelle")
    NEEDS_ANALYSIS = "needs_analysis", _("Analyse des besoins")
    NEGOTIATION = "negotiation", _("Négociation")
    WON = "won", _("Gagnée")
    LOST = "lost", _("Perdue")

class OpportunitySource(models.TextChoices):
    WEBSITE = "website", _("Site web")
    REFERRAL = "referral", _("Recommandation")
    PARTNER = "partner", _("Partenaire")
    COLD_CALL = "cold_call", _("Démarchage")
    EXHIBITION = "exhibition", _("Salon/Exposition")
    OTHER = "other", _("Autre")

class LossReason(models.TextChoices):
    PRICE = "price", _("Prix")
    COMPETITOR = "competitor", _("Concurrent")
    TIMING = "timing", _("Timing")
    NO_BUDGET = "no_budget", _("Pas de budget")
    NO_NEED = "no_need", _("Pas de besoin")
    NO_DECISION = "no_decision", _("Pas de décision")
    OTHER = "other", _("Autre")

class Opportunity(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, verbose_name=_("Nom"))
    tier = models.ForeignKey(
        Tiers, 
        on_delete=models.CASCADE, 
        related_name="opportunities", 
        verbose_name=_("Tiers")
    )
    stage = models.CharField(
        max_length=20,
        choices=OpportunityStatus.choices,
        default=OpportunityStatus.NEW,
        verbose_name=_("Étape")
    )
    estimated_amount = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        verbose_name=_("Montant estimé")
    )
    probability = models.IntegerField(default=10, verbose_name=_("Probabilité (%)"))
    expected_close_date = models.DateField(verbose_name=_("Date de clôture prévue"))
    source = models.CharField(
        max_length=20,
        choices=OpportunitySource.choices,
        default=OpportunitySource.OTHER,
        verbose_name=_("Source")
    )
    description = models.TextField(blank=True, null=True, verbose_name=_("Description"))
    assigned_to = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("Assigné à"))
    
    # Dates
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Créé le"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Mis à jour le"))
    closed_at = models.DateTimeField(blank=True, null=True, verbose_name=_("Clôturé le"))
    
    # Champs pour les opportunités perdues
    loss_reason = models.CharField(
        max_length=20,
        choices=LossReason.choices,
        blank=True,
        null=True,
        verbose_name=_("Raison de perte")
    )
    loss_description = models.TextField(blank=True, null=True, verbose_name=_("Description de la perte"))
    
    # Champs pour les opportunités gagnées
    project_id = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("ID du projet"))
    
    class Meta:
        verbose_name = _("Opportunité")
        verbose_name_plural = _("Opportunités")
        ordering = ["-created_at"]
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        # Mettre à jour la probabilité en fonction du statut
        if self.stage == OpportunityStatus.NEW:
            self.probability = 10
        elif self.stage == OpportunityStatus.NEEDS_ANALYSIS:
            self.probability = 30
        elif self.stage == OpportunityStatus.NEGOTIATION:
            self.probability = 60
        elif self.stage == OpportunityStatus.WON:
            self.probability = 100
            if not self.closed_at:
                self.closed_at = timezone.now()
        elif self.stage == OpportunityStatus.LOST:
            self.probability = 0
            if not self.closed_at:
                self.closed_at = timezone.now()
        
        super().save(*args, **kwargs) 