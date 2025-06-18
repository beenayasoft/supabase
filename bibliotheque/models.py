from django.db import models

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
    
    class Meta:
        verbose_name = "Catégorie"
        verbose_name_plural = "Catégories"
        ordering = ['nom']
    
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
    
    class Meta:
        verbose_name = "Fourniture"
        verbose_name_plural = "Fournitures"
        ordering = ['nom']
    
    def __str__(self):
        return f"{self.nom} ({self.unite})"

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
    
    class Meta:
        verbose_name = "Main d'œuvre"
        verbose_name_plural = "Main d'œuvre"
        ordering = ['nom']
    
    def __str__(self):
        return f"{self.nom} ({self.cout_horaire}€/h)"
