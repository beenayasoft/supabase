from django.shortcuts import render
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.contenttypes.models import ContentType
from .models import Categorie, Fourniture, MainOeuvre, Ouvrage, IngredientOuvrage
from .serializers import (
    CategorieSerializer, CategorieDetailSerializer,
    FournitureSerializer, FournitureDetailSerializer,
    MainOeuvreSerializer, MainOeuvreDetailSerializer,
    OuvrageSerializer, OuvrageDetailSerializer,
    IngredientOuvrageSerializer, IngredientOuvrageCreateSerializer
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

class OuvrageViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour gérer les opérations CRUD sur les ouvrages.
    
    list: Récupère tous les ouvrages
    retrieve: Récupère un ouvrage par son ID
    create: Crée un nouvel ouvrage
    update: Met à jour un ouvrage existant
    partial_update: Met à jour partiellement un ouvrage
    destroy: Supprime un ouvrage
    """
    queryset = Ouvrage.objects.all()
    serializer_class = OuvrageSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['categorie', 'unite']
    search_fields = ['nom', 'description', 'code']
    ordering_fields = ['nom']
    
    def get_serializer_class(self):
        """
        Utilise le sérialiseur détaillé pour les opérations de lecture individuelles.
        """
        if self.action == 'retrieve':
            return OuvrageDetailSerializer
        return OuvrageSerializer
    
    @action(detail=False, methods=['get'])
    def par_categorie(self, request):
        """
        Endpoint pour récupérer les ouvrages filtrés par catégorie.
        """
        categorie_id = request.query_params.get('categorie_id')
        if not categorie_id:
            return Response(
                {"detail": "Le paramètre categorie_id est requis"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            categorie = Categorie.objects.get(pk=categorie_id)
            ouvrages = Ouvrage.objects.filter(categorie=categorie)
            serializer = OuvrageSerializer(ouvrages, many=True)
            return Response(serializer.data)
        except Categorie.DoesNotExist:
            return Response(
                {"detail": "Catégorie non trouvée"}, 
                status=status.HTTP_404_NOT_FOUND
            )

class IngredientOuvrageViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour gérer les opérations CRUD sur les ingrédients d'ouvrages.
    
    list: Récupère tous les ingrédients d'ouvrages
    retrieve: Récupère un ingrédient d'ouvrage par son ID
    create: Crée un nouvel ingrédient d'ouvrage
    update: Met à jour un ingrédient d'ouvrage existant
    partial_update: Met à jour partiellement un ingrédient d'ouvrage
    destroy: Supprime un ingrédient d'ouvrage
    """
    queryset = IngredientOuvrage.objects.all()
    serializer_class = IngredientOuvrageSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['ouvrage', 'element_type']
    
    def get_serializer_class(self):
        """
        Utilise le sérialiseur de création pour les opérations de création.
        """
        if self.action in ['create', 'update', 'partial_update']:
            return IngredientOuvrageCreateSerializer
        return IngredientOuvrageSerializer
    
    def update(self, request, *args, **kwargs):
        """
        Méthode personnalisée pour la mise à jour, qui gère correctement les erreurs de contrainte d'unicité.
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        # Afficher des informations de débogage
        print(f"Mise à jour de l'ingrédient {instance.id} (ouvrage={instance.ouvrage_id}, element_type={instance.element_type_id}, element_id={instance.element_id})")
        print(f"Données reçues: {request.data}")
        
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        
        # Vérifier si la mise à jour modifie des champs qui pourraient violer la contrainte d'unicité
        if ('ouvrage' in request.data or 'element_type_nom' in request.data or 'element_id' in request.data):
            print("Attention: tentative de modification de champs pouvant violer la contrainte d'unicité")
            
            # Si nous essayons de modifier ces champs, vérifions qu'il n'y a pas déjà un ingrédient avec cette combinaison
            ouvrage_id = request.data.get('ouvrage', instance.ouvrage_id)
            element_type_id = instance.element_type_id  # Par défaut, on garde le même
            element_id = request.data.get('element_id', instance.element_id)
            
            # Si element_type_nom est fourni, nous devons le convertir en element_type_id
            if 'element_type_nom' in request.data:
                element_type_nom = request.data['element_type_nom']
                from django.contrib.contenttypes.models import ContentType
                from bibliotheque.models import Fourniture, MainOeuvre
                
                if element_type_nom == 'fourniture':
                    model_class = Fourniture
                else:  # element_type_nom == 'mainoeuvre'
                    model_class = MainOeuvre
                
                element_type_id = ContentType.objects.get_for_model(model_class).id
            
            # Vérifier s'il existe déjà un ingrédient avec cette combinaison (autre que l'instance actuelle)
            existing = IngredientOuvrage.objects.filter(
                ouvrage_id=ouvrage_id,
                element_type_id=element_type_id,
                element_id=element_id
            ).exclude(id=instance.id).exists()
            
            if existing:
                return Response(
                    {"detail": "Un ingrédient avec cette combinaison existe déjà."},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        self.perform_update(serializer)
        
        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}
        
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def par_ouvrage(self, request):
        """
        Endpoint pour récupérer les ingrédients filtrés par ouvrage.
        """
        ouvrage_id = request.query_params.get('ouvrage_id')
        if not ouvrage_id:
            return Response(
                {"detail": "Le paramètre ouvrage_id est requis"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            ouvrage = Ouvrage.objects.get(pk=ouvrage_id)
            ingredients = IngredientOuvrage.objects.filter(ouvrage=ouvrage)
            serializer = IngredientOuvrageSerializer(ingredients, many=True)
            return Response(serializer.data)
        except Ouvrage.DoesNotExist:
            return Response(
                {"detail": "Ouvrage non trouvé"}, 
                status=status.HTTP_404_NOT_FOUND
            )

