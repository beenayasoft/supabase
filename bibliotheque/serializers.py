from rest_framework import serializers
from .models import Categorie, Fourniture, MainOeuvre

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

class FournitureSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour le modèle Fourniture.
    """
    categorie_nom = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = Fourniture
        fields = ['id', 'nom', 'unite', 'prix_achat_ht', 'categorie', 'categorie_nom', 
                 'description', 'reference']
    
    def get_categorie_nom(self, obj):
        """
        Récupère le nom de la catégorie associée à la fourniture.
        """
        if obj.categorie:
            return obj.categorie.chemin_complet
        return None

class FournitureDetailSerializer(serializers.ModelSerializer):
    """
    Sérialiseur détaillé pour le modèle Fourniture.
    """
    categorie_details = CategorieSerializer(source='categorie', read_only=True)
    
    class Meta:
        model = Fourniture
        fields = ['id', 'nom', 'unite', 'prix_achat_ht', 'categorie', 'categorie_details',
                 'description', 'reference']

class MainOeuvreSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour le modèle MainOeuvre.
    """
    categorie_nom = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = MainOeuvre
        fields = ['id', 'nom', 'cout_horaire', 'categorie', 'categorie_nom', 'description']
    
    def get_categorie_nom(self, obj):
        """
        Récupère le nom de la catégorie associée à la main d'œuvre.
        """
        if obj.categorie:
            return obj.categorie.chemin_complet
        return None

class MainOeuvreDetailSerializer(serializers.ModelSerializer):
    """
    Sérialiseur détaillé pour le modèle MainOeuvre.
    """
    categorie_details = CategorieSerializer(source='categorie', read_only=True)
    
    class Meta:
        model = MainOeuvre
        fields = ['id', 'nom', 'cout_horaire', 'categorie', 'categorie_details', 'description'] 