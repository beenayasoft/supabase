from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from django.utils import timezone

from .models import Tiers, Adresse, Contact, ActiviteTiers
from .serializers import (
    TiersListSerializer, TiersDetailSerializer, TiersCreateUpdateSerializer,
    AdresseSerializer, ContactSerializer, ActiviteTiersSerializer, ActiviteTiersCreateSerializer,
    TiersFrontendSerializer, TiersFrontendOptimizedSerializer
)
from .filters import TiersFilter


class TiersPagination(PageNumberPagination):
    """Pagination optimisée pour les tiers"""
    page_size = 10  # 10 tiers par page par défaut
    page_size_query_param = 'page_size'
    max_page_size = 50  # Maximum 50 tiers par page
    page_query_param = 'page'
    
    def get_paginated_response(self, data):
        """Réponse paginée enrichie pour le frontend"""
        return Response({
            'results': data,
            'pagination': {
                'count': self.page.paginator.count,
                'num_pages': self.page.paginator.num_pages,
                'current_page': self.page.number,
                'page_size': self.get_page_size(self.request),
                'has_next': self.page.has_next(),
                'has_previous': self.page.has_previous(),
                'next_page': self.page.next_page_number() if self.page.has_next() else None,
                'previous_page': self.page.previous_page_number() if self.page.has_previous() else None,
            }
        })


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
    pagination_class = TiersPagination  # OPTIMISATION: Pagination côté backend
    
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

    @action(detail=False, methods=['get'])
    def frontend_format(self, request):
        """Vue ULTRA-OPTIMISÉE pour le frontend avec vraie pagination"""
        # OPTIMISATION 1: Prefetch des relations pour éviter N+1
        queryset = self.get_queryset().select_related().prefetch_related(
            'contacts',
            'adresses'
        )
        
        # OPTIMISATION 2: Appliquer les filtres efficacement
        if 'type' in request.query_params:
            type_filter = request.query_params.get('type')
            if type_filter and type_filter != 'tous':
                # Nouveau système : filtrer par relation
                if hasattr(Tiers._meta.get_field('relation'), 'choices'):
                    queryset = queryset.filter(relation=type_filter.rstrip('s'))
                else:
                    # Fallback pour flags si relation n'existe pas encore
                    queryset = queryset.filter(flags__contains=[type_filter.rstrip('s')])
        
        # OPTIMISATION 3: Recherche efficace avec distinct minimal
        search = request.query_params.get('search', '')
        if search:
            queryset = queryset.filter(
                Q(nom__icontains=search) |
                Q(contacts__email__icontains=search) |
                Q(contacts__telephone__icontains=search) |
                Q(contacts__nom__icontains=search) |
                Q(contacts__prenom__icontains=search) |
                Q(siret__icontains=search)
            ).distinct()
        
        # OPTIMISATION 4: Vraie pagination côté backend
        page = self.paginate_queryset(queryset)
        if page is not None:
            # Ajouter les données prefetch aux objets pour éviter les requêtes
            for tier in page:
                tier._prefetched_contacts = list(tier.contacts.all())
                tier._prefetched_adresses = list(tier.adresses.all())
            
            serializer = TiersFrontendOptimizedSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        # Fallback sans pagination (déconseillé avec 1000+ enregistrements)
        for tier in queryset:
            tier._prefetched_contacts = list(tier.contacts.all())
            tier._prefetched_adresses = list(tier.adresses.all())
        
        serializer = TiersFrontendOptimizedSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Endpoint dédié pour les statistiques globales des tiers"""
        try:
            # Récupérer TOUS les tiers (sans pagination) pour calculer les vraies stats
            all_queryset = self.get_queryset()
            
            # Appliquer seulement le filtre de recherche si présent (pas la pagination)
            search = request.query_params.get('search', '')
            if search:
                all_queryset = all_queryset.filter(
                    Q(nom__icontains=search) |
                    Q(contacts__email__icontains=search) |
                    Q(contacts__telephone__icontains=search) |
                    Q(contacts__nom__icontains=search) |
                    Q(contacts__prenom__icontains=search) |
                    Q(siret__icontains=search)
                ).distinct()
            
            # Calculer les stats par relation/type
            stats = {
                'total': all_queryset.count(),
                'client': all_queryset.filter(relation='client').count(),
                'fournisseur': all_queryset.filter(relation='fournisseur').count(),
                'prospect': all_queryset.filter(relation='prospect').count(),
                'sous_traitant': all_queryset.filter(relation='sous_traitant').count(),
            }
            
            # Fallback pour l'ancien système flags si nécessaire
            if stats['total'] == 0:
                stats = {
                    'total': all_queryset.count(),
                    'client': all_queryset.filter(flags__contains=['client']).count(),
                    'fournisseur': all_queryset.filter(flags__contains=['fournisseur']).count(),
                    'prospect': all_queryset.filter(flags__contains=['prospect']).count(),
                    'sous_traitant': all_queryset.filter(flags__contains=['sous_traitant']).count(),
                }
            
            return Response(stats)
            
        except Exception as e:
            return Response(
                {'error': f'Erreur lors du calcul des stats: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def frontend_format_legacy(self, request):
        """ANCIENNE vue pour le frontend - garde pour compatibilité"""
        queryset = self.get_queryset()
        # Appliquer les filtres
        if 'type' in request.query_params:
            type_filter = request.query_params.get('type')
            if type_filter and type_filter != 'tous':
                queryset = queryset.filter(flags__contains=[type_filter.rstrip('s')])
        
        # Appliquer la recherche
        search = request.query_params.get('search', '')
        if search:
            queryset = queryset.filter(
                Q(nom__icontains=search) |
                Q(contacts__email__icontains=search) |
                Q(contacts__telephone__icontains=search) |
                Q(contacts__nom__icontains=search) |
                Q(contacts__prenom__icontains=search) |
                Q(siret__icontains=search)
            ).distinct()
        
        # Pagination
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = TiersFrontendSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = TiersFrontendSerializer(queryset, many=True)
        return Response(serializer.data)


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