from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Categorie
from .serializers import CategorieSerializer, CategorieDetailSerializer

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
