from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from django.utils import timezone

from .models import Tiers, Adresse, Contact, ActiviteTiers
from .serializers import (
    TiersListSerializer, TiersDetailSerializer, TiersCreateUpdateSerializer,
    AdresseSerializer, ContactSerializer, ActiviteTiersSerializer, ActiviteTiersCreateSerializer
)
from .filters import TiersFilter

class TiersViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour gérer les tiers avec CRUD complet et fonctionnalités avancées
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = TiersFilter
    search_fields = ['nom', 'siret', 'tva']
    ordering_fields = ['nom', 'date_creation', 'date_modification']
    ordering = ['-date_creation']
    
    def get_queryset(self):
        """Filtrer les tiers non archivés par défaut"""
        queryset = Tiers.objects.filter(is_deleted=False)
        
        # Filtre pour les archivés si demandé
        show_archived = self.request.query_params.get('archived', 'false').lower() == 'true'
        if show_archived:
            queryset = Tiers.objects.all()
        
        # Filtre par utilisateur assigné (sauf pour les superusers)
        #if not self.request.user.is_superuser:
         #   queryset = queryset.filter(assigned_user=self.request.user)

         #une solution plus flexible en attendant de tout developper/ à supprimer si possible
          # Voir les tiers assignés à l'utilisateur OU sans assignation
        Q(assigned_user=self.request.user) | Q(assigned_user__isnull=True)
        return queryset
    
    def get_serializer_class(self):
        """Choisir le serializer approprié selon l'action"""
        if self.action == 'list':
            return TiersListSerializer
        elif self.action in ['retrieve', 'vue_360']:
            return TiersDetailSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return TiersCreateUpdateSerializer
        return TiersListSerializer
    
    def perform_destroy(self, instance):
        """Soft delete au lieu de supprimer définitivement"""
        instance.delete()  # Utilise la méthode soft delete du modèle
    
    @action(detail=True, methods=['get'])
    def vue_360(self, request, pk=None):
        """Vue 360° d'un tier avec toutes les informations groupées"""
        tier = self.get_object()
        serializer = self.get_serializer(tier)
        
        # Structurer la réponse avec des onglets
        data = serializer.data
        data['onglets'] = {
            'infos': {
                'adresses': data.pop('adresses', [])
            },
            'contacts': data.pop('contacts', []),
            'activites': data.pop('activites', [])
        }
        
        return Response(data)
    
    @action(detail=True, methods=['post'])
    def activites(self, request, pk=None):
        """Ajouter une activité manuelle à un tier"""
        tier = self.get_object()
        serializer = ActiviteTiersCreateSerializer(
            data=request.data,
            context={'request': request, 'tier': tier}
        )
        
        if serializer.is_valid():
            activite = serializer.save()
            return Response(
                ActiviteTiersSerializer(activite).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def contacts(self, request, pk=None):
        """Ajouter un contact à un tier"""
        tier = self.get_object()
        serializer = ContactSerializer(data=request.data)
        
        if serializer.is_valid():
            contact = serializer.save(tier=tier)
            
            # Créer une activité
            ActiviteTiers.objects.create(
                tier=tier,
                type=ActiviteTiers.TYPE_MODIFICATION,
                utilisateur=request.user,
                contenu=f"Contact ajouté : {contact.prenom} {contact.nom}"
            )
            
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def adresses(self, request, pk=None):
        """Ajouter une adresse à un tier"""
        tier = self.get_object()
        serializer = AdresseSerializer(data=request.data)
        
        if serializer.is_valid():
            adresse = serializer.save(tier=tier)
            
            # Créer une activité
            ActiviteTiers.objects.create(
                tier=tier,
                type=ActiviteTiers.TYPE_MODIFICATION,
                utilisateur=request.user,
                contenu=f"Adresse ajoutée : {adresse.libelle}"
            )
            
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def restaurer(self, request, pk=None):
        """Restaurer un tier archivé"""
        tier = self.get_object()
        if not tier.is_deleted:
            return Response(
                {"error": "Ce tier n'est pas archivé"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        tier.restore()
        
        # Créer une activité
        ActiviteTiers.objects.create(
            tier=tier,
            type=ActiviteTiers.TYPE_MODIFICATION,
            utilisateur=request.user,
            contenu="Tier restauré"
        )
        
        return Response({"message": "Tier restauré avec succès"})


class AdresseViewSet(viewsets.ModelViewSet):
    """ViewSet pour gérer les adresses indépendamment"""
    queryset = Adresse.objects.all()
    serializer_class = AdresseSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['tier', 'facturation']


class ContactViewSet(viewsets.ModelViewSet):
    """ViewSet pour gérer les contacts indépendamment"""
    queryset = Contact.objects.all()
    serializer_class = ContactSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['tier', 'contact_principal_devis', 'contact_principal_facture']


class ActiviteTiersViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet pour consulter les activités (lecture seule)"""
    queryset = ActiviteTiers.objects.all()
    serializer_class = ActiviteTiersSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['tier', 'type', 'utilisateur']
    ordering_fields = ['date']
    ordering = ['-date']