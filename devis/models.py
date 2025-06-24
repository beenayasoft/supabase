from django.db import models
from django.db.models import Sum, F, DecimalField, ExpressionWrapper
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from tiers.models import Tiers
from bibliotheque.models import Ouvrage

class Devis(models.Model):
    """
    Modèle pour représenter un devis.
    """
    STATUT_CHOICES = [
        ('brouillon', 'Brouillon'),
        ('envoyé', 'Envoyé'),
        ('accepté', 'Accepté'),
        ('refusé', 'Refusé'),
        ('annulé', 'Annulé'),
    ]
    
    client = models.ForeignKey(
        Tiers, 
        on_delete=models.CASCADE, 
        related_name='devis',
        verbose_name="Client"
    )
    objet = models.CharField(max_length=255, verbose_name="Objet du devis")
    statut = models.CharField(
        max_length=20, 
        choices=STATUT_CHOICES, 
        default='brouillon',
        verbose_name="Statut"
    )
    numero = models.CharField(
        max_length=50, 
        unique=True,
        verbose_name="Numéro de devis"
    )
    date_creation = models.DateField(auto_now_add=True, verbose_name="Date de création")
    date_validite = models.DateField(
        null=True, 
        blank=True,
        verbose_name="Date de validité"
    )
    commentaire = models.TextField(blank=True, null=True, verbose_name="Commentaire")
    conditions_paiement = models.TextField(
        blank=True, 
        null=True,
        verbose_name="Conditions de paiement"
    )
    marge_globale = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        null=True, 
        blank=True,
        verbose_name="Marge globale (%)"
    )
    
    # Relation avec l'opportunité (si le devis est créé à partir d'une opportunité)
    opportunity = models.ForeignKey(
        'opportunite.Opportunity',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='devis',
        verbose_name="Opportunité"
    )
    
    class Meta:
        verbose_name = "Devis"
        verbose_name_plural = "Devis"
        ordering = ['-date_creation', 'numero']
    
    def __str__(self):
        return f"Devis {self.numero} - {self.client.nom} - {self.objet}"
    
    @property
    def total_ht(self):
        """
        Calcule le montant total HT du devis en sommant les totaux des lots.
        """
        from django.db.models import Sum, F
        
        # Récupérer toutes les lignes de tous les lots de ce devis
        lignes_query = LigneDevis.objects.filter(lot__devis=self)
        
        # Calculer le total HT
        total = lignes_query.annotate(
            total_ligne=F('prix_unitaire') * F('quantite')
        ).aggregate(
            total=Sum('total_ligne')
        )['total'] or 0
        
        return total
    
    @property
    def total_debourse(self):
        """
        Calcule le montant total du déboursé sec du devis en sommant les déboursés des lignes.
        """
        from django.db.models import Sum, F
        
        # Récupérer toutes les lignes de tous les lots de ce devis
        lignes_query = LigneDevis.objects.filter(lot__devis=self)
        
        # Calculer le total du déboursé
        total = lignes_query.annotate(
            total_debourse_ligne=F('debourse') * F('quantite')
        ).aggregate(
            total=Sum('total_debourse_ligne')
        )['total'] or 0
        
        return total
    
    @property
    def marge_totale(self):
        """
        Calcule la marge totale du devis en pourcentage.
        Formule : (Prix de vente - Déboursé) / Prix de vente * 100
        """
        total_ht = self.total_ht
        total_debourse = self.total_debourse
        
        if total_ht == 0:
            return 0
        
        return ((total_ht - total_debourse) / total_ht) * 100

class Lot(models.Model):
    """
    Modèle pour représenter un lot dans un devis.
    """
    devis = models.ForeignKey(
        Devis, 
        on_delete=models.CASCADE, 
        related_name='lots',
        verbose_name="Devis"
    )
    nom = models.CharField(max_length=100, verbose_name="Nom du lot")
    ordre = models.PositiveIntegerField(default=0, verbose_name="Ordre d'affichage")
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    
    class Meta:
        verbose_name = "Lot"
        verbose_name_plural = "Lots"
        ordering = ['devis', 'ordre', 'nom']
        unique_together = ('devis', 'ordre')
    
    def __str__(self):
        return f"{self.nom} - {self.devis.numero}"
    
    @property
    def total_ht(self):
        """
        Calcule le montant total HT du lot.
        """
        total = self.lignes.aggregate(
            total=Sum(F('prix_unitaire') * F('quantite'))
        )['total'] or 0
        return total
    
    @property
    def total_debourse(self):
        """
        Calcule le montant total du déboursé sec du lot.
        """
        total = self.lignes.aggregate(
            total=Sum(F('debourse') * F('quantite'))
        )['total'] or 0
        return total
    
    @property
    def marge(self):
        """
        Calcule la marge du lot en pourcentage.
        """
        total_ht = self.total_ht
        total_debourse = self.total_debourse
        
        if total_ht == 0:
            return 0
        
        return ((total_ht - total_debourse) / total_ht) * 100

class LigneDevis(models.Model):
    """
    Modèle pour représenter une ligne dans un devis.
    Une ligne peut être soit liée à un ouvrage de la bibliothèque,
    soit être une ligne manuelle.
    """
    TYPE_CHOICES = [
        ('ouvrage', 'Ouvrage de la bibliothèque'),
        ('manuel', 'Ligne manuelle'),
    ]
    
    lot = models.ForeignKey(
        Lot, 
        on_delete=models.CASCADE, 
        related_name='lignes',
        verbose_name="Lot"
    )
    type = models.CharField(
        max_length=20, 
        choices=TYPE_CHOICES, 
        default='manuel',
        verbose_name="Type de ligne"
    )
    ouvrage = models.ForeignKey(
        Ouvrage, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='lignes_devis',
        verbose_name="Ouvrage"
    )
    description = models.CharField(max_length=255, verbose_name="Description")
    quantite = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        verbose_name="Quantité"
    )
    unite = models.CharField(max_length=20, verbose_name="Unité")
    prix_unitaire = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        verbose_name="Prix unitaire HT"
    )
    debourse = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        verbose_name="Déboursé sec unitaire"
    )
    ordre = models.PositiveIntegerField(default=0, verbose_name="Ordre d'affichage")
    
    class Meta:
        verbose_name = "Ligne de devis"
        verbose_name_plural = "Lignes de devis"
        ordering = ['lot', 'ordre']
    
    def __str__(self):
        return f"{self.description} ({self.quantite} {self.unite})"
    
    @property
    def total_ht(self):
        """
        Calcule le montant total HT de la ligne.
        """
        return self.prix_unitaire * self.quantite
    
    @property
    def total_debourse(self):
        """
        Calcule le montant total du déboursé sec de la ligne.
        """
        return self.debourse * self.quantite
    
    @property
    def marge(self):
        """
        Calcule la marge de la ligne en pourcentage.
        """
        if self.prix_unitaire == 0:
            return 0
        
        return ((self.prix_unitaire - self.debourse) / self.prix_unitaire) * 100
    
    def save(self, *args, **kwargs):
        """
        Surcharge de la méthode save pour initialiser les valeurs depuis l'ouvrage
        si le type est 'ouvrage'.
        """
        if self.type == 'ouvrage' and self.ouvrage and not self.id:
            # Si c'est une nouvelle ligne de type 'ouvrage', on initialise les valeurs
            # depuis l'ouvrage associé
            self.description = self.ouvrage.nom
            self.unite = self.ouvrage.unite
            
            # On arrondit le déboursé à 2 décimales
            from decimal import Decimal, ROUND_HALF_UP
            debourse = self.ouvrage.debourse_sec
            self.debourse = round(debourse, 2)
            
            # Par défaut, on initialise le prix unitaire avec une marge de 30%
            # si le déboursé est > 0, sinon on met 0
            if self.debourse > 0:
                # On arrondit à 2 décimales et on s'assure de ne pas dépasser 10 chiffres au total
                prix = (self.debourse / Decimal('0.7')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                # Vérifier que le nombre ne dépasse pas 10 chiffres au total
                if len(str(prix).replace('.', '')) > 10:
                    prix = Decimal('9999999.99')
                self.prix_unitaire = prix
            else:
                self.prix_unitaire = 0
        
        super().save(*args, **kwargs)
