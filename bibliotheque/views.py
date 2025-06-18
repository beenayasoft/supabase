from django.shortcuts import render
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Categorie, Fourniture, MainOeuvre
from .serializers import (
    CategorieSerializer, CategorieDetailSerializer,
    FournitureSerializer, FournitureDetailSerializer,
    MainOeuvreSerializer, MainOeuvreDetailSerializer
)

# Create your views here.

class CategorieViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour gérer les opérations CRUD sur les catégories.
    
    list: Récupère toutes les catégories
    retrieve: Récupère une catégorie par son ID
    create: Crée une nouvelle catégorie
    update: Met à jour une catégorie existante
    partial_update: Met à jour partiellement une catégorie
    destroy: Supprime une catégorie
    """
    queryset = Categorie.objects.all()
    serializer_class = CategorieSerializer
    
    def get_serializer_class(self):
        """
        Utilise le sérialiseur détaillé pour les opérations de lecture individuelles.
        """
        if self.action == 'retrieve':
            return CategorieDetailSerializer
        return CategorieSerializer
    
    @action(detail=False, methods=['get'])
    def racines(self, request):
        """
        Endpoint pour récupérer uniquement les catégories racines (sans parent).
        """
        racines = Categorie.objects.filter(parent=None)
        serializer = CategorieDetailSerializer(racines, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def sous_categories(self, request, pk=None):
        """
        Endpoint pour récupérer toutes les sous-catégories directes d'une catégorie.
        """
        try:
            categorie = self.get_object()
            sous_categories = Categorie.objects.filter(parent=categorie)
            serializer = CategorieSerializer(sous_categories, many=True)
            return Response(serializer.data)
        except Categorie.DoesNotExist:
            return Response(
                {"detail": "Catégorie non trouvée"}, 
                status=status.HTTP_404_NOT_FOUND
            )

class FournitureViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour gérer les opérations CRUD sur les fournitures.
    
    list: Récupère toutes les fournitures
    retrieve: Récupère une fourniture par son ID
    create: Crée une nouvelle fourniture
    update: Met à jour une fourniture existante
    partial_update: Met à jour partiellement une fourniture
    destroy: Supprime une fourniture
    """
    queryset = Fourniture.objects.all()
    serializer_class = FournitureSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['categorie', 'unite']
    search_fields = ['nom', 'description', 'reference']
    ordering_fields = ['nom', 'prix_achat_ht']
    
    def get_serializer_class(self):
        """
        Utilise le sérialiseur détaillé pour les opérations de lecture individuelles.
        """
        if self.action == 'retrieve':
            return FournitureDetailSerializer
        return FournitureSerializer
    
    @action(detail=False, methods=['get'])
    def par_categorie(self, request):
        """
        Endpoint pour récupérer les fournitures filtrées par catégorie.
        """
        categorie_id = request.query_params.get('categorie_id')
        if not categorie_id:
            return Response(
                {"detail": "Le paramètre categorie_id est requis"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            categorie = Categorie.objects.get(pk=categorie_id)
            fournitures = Fourniture.objects.filter(categorie=categorie)
            serializer = FournitureSerializer(fournitures, many=True)
            return Response(serializer.data)
        except Categorie.DoesNotExist:
            return Response(
                {"detail": "Catégorie non trouvée"}, 
                status=status.HTTP_404_NOT_FOUND
            )

class MainOeuvreViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour gérer les opérations CRUD sur les types de main d'œuvre.
    
    list: Récupère tous les types de main d'œuvre
    retrieve: Récupère un type de main d'œuvre par son ID
    create: Crée un nouveau type de main d'œuvre
    update: Met à jour un type de main d'œuvre existant
    partial_update: Met à jour partiellement un type de main d'œuvre
    destroy: Supprime un type de main d'œuvre
    """
    queryset = MainOeuvre.objects.all()
    serializer_class = MainOeuvreSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['categorie']
    search_fields = ['nom', 'description']
    ordering_fields = ['nom', 'cout_horaire']
    
    def get_serializer_class(self):
        """
        Utilise le sérialiseur détaillé pour les opérations de lecture individuelles.
        """
        if self.action == 'retrieve':
            return MainOeuvreDetailSerializer
        return MainOeuvreSerializer
    
    @action(detail=False, methods=['get'])
    def par_categorie(self, request):
        """
        Endpoint pour récupérer les types de main d'œuvre filtrés par catégorie.
        """
        categorie_id = request.query_params.get('categorie_id')
        if not categorie_id:
            return Response(
                {"detail": "Le paramètre categorie_id est requis"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            categorie = Categorie.objects.get(pk=categorie_id)
            main_oeuvre = MainOeuvre.objects.filter(categorie=categorie)
            serializer = MainOeuvreSerializer(main_oeuvre, many=True)
            return Response(serializer.data)
        except Categorie.DoesNotExist:
            return Response(
                {"detail": "Catégorie non trouvée"}, 
                status=status.HTTP_404_NOT_FOUND
            )
