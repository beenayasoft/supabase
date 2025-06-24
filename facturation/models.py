from django.db import models
from django.conf import settings
from devis.models import Devis, LigneDevis

class TypeFacture(models.TextChoices):
    ACOMPTE = 'acompte', 'Acompte'
    SOLDE = 'solde', 'Solde'
    AVANCEMENT = 'avancement', 'Avancement'

class StatutFacture(models.TextChoices):
    BROUILLON = 'brouillon', 'Brouillon'
    EMISE = 'emise', 'Émise'
    PAYEE_PARTIELLEMENT = 'payee_partiellement', 'Payée partiellement'
    PAYEE = 'payee', 'Payée'

class Facture(models.Model):
    devis = models.OneToOneField(
        Devis,
        on_delete=models.PROTECT,
        related_name='facture',
        limit_choices_to={'statut': 'accepte'},  # Uniquement les devis acceptés
        verbose_name="Devis lié"
    )
    type = models.CharField(
        max_length=20,
        choices=TypeFacture.choices,
        default=TypeFacture.SOLDE,
        verbose_name="Type de facture"
    )
    date_emission = models.DateField(auto_now_add=True, verbose_name="Date d'émission")
    statut = models.CharField(
        max_length=30,
        choices=StatutFacture.choices,
        default=StatutFacture.BROUILLON,
        verbose_name="Statut"
    )
    total_ht = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Total HT")
    montant_payé = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Montant payé")
    reste_a_payer = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Reste à payer")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Créé par"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Facture"
        verbose_name_plural = "Factures"
        ordering = ['-date_emission', '-created_at']

    def __str__(self):
        return f"Facture #{self.id} - {self.devis}"

    def calculer_total_ht(self):
        total = sum(ligne.sous_total_ht for ligne in self.lignes.all())
        self.total_ht = total
        return total

    def calculer_reste_a_payer(self):
        self.reste_a_payer = self.total_ht - self.montant_payé
        return self.reste_a_payer

    def save(self, *args, **kwargs):
        self.calculer_total_ht()
        self.calculer_reste_a_payer()
        super().save(*args, **kwargs)

class LigneFacture(models.Model):
    facture = models.ForeignKey(
        Facture,
        on_delete=models.CASCADE,
        related_name='lignes',
        verbose_name="Facture"
    )
    designation = models.CharField(max_length=255, verbose_name="Désignation")
    quantite = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Quantité")
    unite = models.CharField(max_length=50, verbose_name="Unité")
    prix_unitaire = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Prix unitaire HT")
    sous_total_ht = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Sous-total HT")

    class Meta:
        verbose_name = "Ligne de facture"
        verbose_name_plural = "Lignes de facture"

    def __str__(self):
        return f"{self.designation} ({self.quantite} {self.unite})"

    def save(self, *args, **kwargs):
        self.sous_total_ht = self.quantite * self.prix_unitaire
        super().save(*args, **kwargs)

class PaiementFacture(models.Model):
    facture = models.ForeignKey(
        Facture,
        on_delete=models.CASCADE,
        related_name='paiements',
        verbose_name="Facture"
    )
    montant = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Montant payé")
    date_paiement = models.DateField(auto_now_add=True, verbose_name="Date de paiement")
    moyen = models.CharField(max_length=100, verbose_name="Moyen de paiement", blank=True, null=True)
    reference = models.CharField(max_length=100, verbose_name="Référence", blank=True, null=True)

    class Meta:
        verbose_name = "Paiement de facture"
        verbose_name_plural = "Paiements de facture"

    def __str__(self):
        return f"{self.montant}€ le {self.date_paiement}"
