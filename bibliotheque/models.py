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
