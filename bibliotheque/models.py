from django.db import models
from django.db.models import Sum, F, DecimalField, ExpressionWrapper
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

# Create your models here.

class Categorie(models.Model):
    """
    Modèle pour représenter les catégories hiérarchiques dans la bibliothèque d'ouvrages.
    Une catégorie peut avoir un parent, créant ainsi une structure arborescente.
    """
    nom = models.CharField(max_length=100, verbose_name="Nom de la catégorie")
    parent = models.ForeignKey(
        'self', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='sous_categories',
        verbose_name="Catégorie parente"
    )
    position = models.PositiveIntegerField(default=0, verbose_name="Position d'affichage")
    
    class Meta:
        verbose_name = "Catégorie"
        verbose_name_plural = "Catégories"
        ordering = ['position', 'nom']
    
    def __str__(self):
        return self.nom
    
    @property
    def chemin_complet(self):
        """
        Retourne le chemin complet de la catégorie (ex: "Maçonnerie > Murs")
        """
        if self.parent:
            return f"{self.parent.chemin_complet} > {self.nom}"
        return self.nom

class Fourniture(models.Model):
    """
    Modèle pour représenter les fournitures (matériaux, produits, etc.) utilisées dans les ouvrages.
    """
    nom = models.CharField(max_length=100, verbose_name="Nom de la fourniture")
    unite = models.CharField(max_length=20, verbose_name="Unité de mesure")
    prix_achat_ht = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        verbose_name="Prix d'achat HT"
    )
    categorie = models.ForeignKey(
        Categorie, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='fournitures',
        verbose_name="Catégorie"
    )
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    reference = models.CharField(
        max_length=50, 
        blank=True, 
        null=True, 
        verbose_name="Référence"
    )
    supplier = models.CharField(
        max_length=100, 
        blank=True, 
        null=True, 
        verbose_name="Fournisseur"
    )
    vat_rate = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=20.0,
        verbose_name="Taux TVA (%)"
    )
    # Nouveaux champs manquants pour cohérence frontend
    type = models.CharField(
        max_length=20,
        default="material",
        verbose_name="Type"
    )
    code = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="Code"
    )
    created_at = models.DateTimeField(auto_now_add=True, null=True, verbose_name="Créé le")
    updated_at = models.DateTimeField(auto_now=True, null=True, verbose_name="Mis à jour le")
    
    class Meta:
        verbose_name = "Fourniture"
        verbose_name_plural = "Fournitures"
        ordering = ['nom']
    
    def __str__(self):
        return f"{self.nom} ({self.unite})"
    
    @property
    def unitPrice(self):
        """Alias pour prix_achat_ht (compatibilité frontend)"""
        return self.prix_achat_ht
    
    @property
    def vatRate(self):
        """Alias pour vat_rate (compatibilité frontend)"""
        return float(self.vat_rate)

class MainOeuvre(models.Model):
    """
    Modèle pour représenter les différents types de main d'œuvre avec leur coût horaire.
    """
    nom = models.CharField(max_length=100, verbose_name="Nom du type de main d'œuvre")
    cout_horaire = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        verbose_name="Coût horaire"
    )
    categorie = models.ForeignKey(
        Categorie, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='main_oeuvre',
        verbose_name="Catégorie"
    )
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    # Nouveaux champs manquants pour cohérence frontend
    type = models.CharField(
        max_length=20,
        default="labor",
        verbose_name="Type"
    )
    unite = models.CharField(
        max_length=20,
        default="h",
        verbose_name="Unité de mesure"
    )
    code = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="Code"
    )
    created_at = models.DateTimeField(auto_now_add=True, null=True, verbose_name="Créé le")
    updated_at = models.DateTimeField(auto_now=True, null=True, verbose_name="Mis à jour le")
    
    class Meta:
        verbose_name = "Main d'œuvre"
        verbose_name_plural = "Main d'œuvre"
        ordering = ['nom']
    
    def __str__(self):
        return f"{self.nom} ({self.cout_horaire}€/h)"
    
    @property
    def unitPrice(self):
        """Alias pour cout_horaire (compatibilité frontend)"""
        return self.cout_horaire
    
    @property
    def prix_achat_ht(self):
        """Alias pour cout_horaire (compatibilité)"""
        return self.cout_horaire

class Ouvrage(models.Model):
    """
    Modèle pour représenter les ouvrages composés, qui sont des assemblages
    d'ingrédients (fournitures et main d'œuvre) avec leurs quantités.
    """
    nom = models.CharField(max_length=200, verbose_name="Nom de l'ouvrage")
    unite = models.CharField(max_length=20, verbose_name="Unité de mesure")
    categorie = models.ForeignKey(
        Categorie, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='ouvrages',
        verbose_name="Catégorie"
    )
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    code = models.CharField(
        max_length=50, 
        blank=True, 
        null=True, 
        verbose_name="Code/Référence"
    )
    
    prix_recommande = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=0,
        verbose_name="Prix recommandé"
    )
    marge = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=20.0,
        verbose_name="Marge (%)"
    )
    is_custom = models.BooleanField(
        default=False,
        verbose_name="Ouvrage personnalisé"
    )
    # Champs additionnels pour cohérence frontend
    type = models.CharField(
        max_length=20,
        default="work",
        verbose_name="Type"
    )
    complexity = models.CharField(
        max_length=20,
        choices=[('low', 'Faible'), ('medium', 'Moyenne'), ('high', 'Élevée')],
        default='medium',
        verbose_name="Complexité"
    )
    efficiency = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=1.0,
        verbose_name="Rendement"
    )
    
    created_at = models.DateTimeField(auto_now_add=True, null=True, verbose_name="Créé le")
    updated_at = models.DateTimeField(auto_now=True, null=True, verbose_name="Mis à jour le")
    
    class Meta:
        verbose_name = "Ouvrage"
        verbose_name_plural = "Ouvrages"
        ordering = ['nom']
    
    def __str__(self):
        return f"{self.nom} ({self.unite})"
    
    @property
    def debourse_sec(self):
        """
        Calcule le déboursé sec (coût total) de l'ouvrage en fonction des ingrédients et quantités.
        """
        total = 0
        for ingredient in self.ingredients.all():
            total += ingredient.cout_total
        return total
    
    @property
    def totalCost(self):
        """Alias pour debourse_sec (compatibilité frontend)"""
        return self.debourse_sec
    
    @property
    def recommendedPrice(self):
        """Prix recommandé calculé ou défini manuellement"""
        if self.prix_recommande > 0:
            return self.prix_recommande
        cout_total = self.debourse_sec
        if cout_total > 0:
            return cout_total * (1 + float(self.marge) / 100)
        return 0
    
    @property
    def margin(self):
        """Alias pour marge (compatibilité frontend)"""
        return float(self.marge)
    
    @property
    def laborCost(self):
        """Calcule le coût total de la main d'œuvre"""
        total = 0
        for ingredient in self.ingredients.all():
            if ingredient.element_type.model == 'mainoeuvre':
                total += ingredient.cout_total
        return total
    
    @property
    def materialCost(self):
        """Calcule le coût total des matériaux"""
        total = 0
        for ingredient in self.ingredients.all():
            if ingredient.element_type.model == 'fourniture':
                total += ingredient.cout_total
        return total

class IngredientOuvrage(models.Model):
    """
    Modèle pour représenter les ingrédients d'un ouvrage avec leurs quantités.
    Utilise une relation générique pour pointer soit vers une fourniture, soit vers un type de main d'œuvre.
    """
    ouvrage = models.ForeignKey(
        Ouvrage, 
        on_delete=models.CASCADE, 
        related_name='ingredients',
        verbose_name="Ouvrage"
    )
    # Champs pour la relation générique
    element_type = models.ForeignKey(
        ContentType, 
        on_delete=models.CASCADE,
        limit_choices_to={'model__in': ('fourniture', 'mainoeuvre')},
        verbose_name="Type d'élément"
    )
    element_id = models.PositiveIntegerField(verbose_name="ID de l'élément")
    element = GenericForeignKey('element_type', 'element_id')
    
    quantite = models.DecimalField(
        max_digits=10, 
        decimal_places=3, 
        verbose_name="Quantité"
    )
    
    class Meta:
        verbose_name = "Ingrédient d'ouvrage"
        verbose_name_plural = "Ingrédients d'ouvrage"
        unique_together = ('ouvrage', 'element_type', 'element_id')
        ordering = ['ouvrage', 'element_type', 'element_id']
    
    def __str__(self):
        return f"{self.element} - {self.quantite}"
    
    @property
    def cout_total(self):
        """
        Calcule le coût total de cet ingrédient (quantité × prix unitaire).
        """
        if self.element_type.model == 'fourniture':
            fourniture = Fourniture.objects.get(id=self.element_id)
            return self.quantite * fourniture.prix_achat_ht
        elif self.element_type.model == 'mainoeuvre':
            main_oeuvre = MainOeuvre.objects.get(id=self.element_id)
            return self.quantite * main_oeuvre.cout_horaire
        return 0
