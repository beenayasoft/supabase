from rest_framework import serializers
from .models import Categorie

class CategorieSerializer(serializers.ModelSerializer):
    """
    Sérialiseur de base pour le modèle Categorie.
    """
    class Meta:
        model = Categorie
        fields = ['id', 'nom', 'parent']

class CategorieDetailSerializer(serializers.ModelSerializer):
    """
    Sérialiseur détaillé pour le modèle Categorie, incluant le chemin complet
    et les sous-catégories.
    """
    sous_categories = serializers.SerializerMethodField()
    chemin_complet = serializers.CharField(read_only=True)
    
    class Meta:
        model = Categorie
        fields = ['id', 'nom', 'parent', 'chemin_complet', 'sous_categories']
    
    def get_sous_categories(self, obj):
        """
        Récupère les sous-catégories de la catégorie actuelle.
        """
        sous_categories = Categorie.objects.filter(parent=obj)
        return CategorieSerializer(sous_categories, many=True).data 