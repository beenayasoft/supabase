from django.shortcuts import render, get_object_or_404
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Devis, Lot, LigneDevis
from .serializers import (
    DevisSerializer, DevisDetailSerializer, DevisCreateSerializer,
    LotSerializer, LotDetailSerializer,
    LigneDevisSerializer, LigneDevisDetailSerializer, LigneDevisCreateSerializer
)
from bibliotheque.models import Ouvrage

class DevisViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour gérer les opérations CRUD sur les devis.
    
    list: Récupère tous les devis
    retrieve: Récupère un devis par son ID
    create: Crée un nouveau devis
    update: Met à jour un devis existant
    partial_update: Met à jour partiellement un devis
    destroy: Supprime un devis
    """
    queryset = Devis.objects.all()
    serializer_class = DevisSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['client', 'statut']
    search_fields = ['numero', 'objet', 'client__nom']
    ordering_fields = ['date_creation', 'numero', 'client__nom', 'statut']
    ordering = ['-date_creation']
    
    def get_serializer_class(self):
        """
        Utilise le sérialiseur approprié en fonction de l'action.
        """
        if self.action == 'retrieve':
            return DevisDetailSerializer
        elif self.action == 'create':
            return DevisCreateSerializer
        return DevisSerializer
    
    @action(detail=True, methods=['post'])
    def duplicate(self, request, pk=None):
        """
        Duplique un devis existant.
        """
        devis = self.get_object()
        
        # Créer un nouveau numéro de devis
        nouveau_numero = f"{devis.numero}-COPIE"
        
        # Créer une copie du devis
        nouveau_devis = Devis.objects.create(
            client=devis.client,
            objet=f"Copie de : {devis.objet}",
            statut='brouillon',
            numero=nouveau_numero,
            date_validite=devis.date_validite,
            commentaire=devis.commentaire,
            conditions_paiement=devis.conditions_paiement,
            marge_globale=devis.marge_globale
        )
        
        # Copier les lots et leurs lignes
        for lot in devis.lots.all():
            nouveau_lot = Lot.objects.create(
                devis=nouveau_devis,
                nom=lot.nom,
                ordre=lot.ordre,
                description=lot.description
            )
            
            # Copier les lignes du lot
            for ligne in lot.lignes.all():
                LigneDevis.objects.create(
                    lot=nouveau_lot,
                    type=ligne.type,
                    ouvrage=ligne.ouvrage,
                    description=ligne.description,
                    quantite=ligne.quantite,
                    unite=ligne.unite,
                    prix_unitaire=ligne.prix_unitaire,
                    debourse=ligne.debourse,
                    ordre=ligne.ordre
                )
        
        # Retourner le nouveau devis
        serializer = DevisDetailSerializer(nouveau_devis)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['put'])
    def change_status(self, request, pk=None):
        """
        Change le statut d'un devis.
        """
        devis = self.get_object()
        nouveau_statut = request.data.get('statut')
        
        if not nouveau_statut:
            return Response(
                {"detail": "Le statut est requis"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if nouveau_statut not in [s[0] for s in Devis.STATUT_CHOICES]:
            return Response(
                {"detail": f"Statut invalide. Valeurs possibles : {[s[0] for s in Devis.STATUT_CHOICES]}"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        devis.statut = nouveau_statut
        devis.save()
        
        serializer = DevisSerializer(devis)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def pdf(self, request, pk=None):
        """
        Génère un PDF pour le devis.
        """
        # Cette fonctionnalité sera implémentée ultérieurement
        return Response(
            {"detail": "La génération de PDF sera implémentée ultérieurement"}, 
            status=status.HTTP_501_NOT_IMPLEMENTED
        )

class LotViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour gérer les opérations CRUD sur les lots.
    
    list: Récupère tous les lots
    retrieve: Récupère un lot par son ID
    create: Crée un nouveau lot
    update: Met à jour un lot existant
    partial_update: Met à jour partiellement un lot
    destroy: Supprime un lot
    """
    queryset = Lot.objects.all()
    serializer_class = LotSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['devis']
    ordering_fields = ['ordre', 'nom']
    ordering = ['ordre', 'nom']
    
    def get_serializer_class(self):
        """
        Utilise le sérialiseur détaillé pour les opérations de lecture individuelles.
        """
        if self.action == 'retrieve':
            return LotDetailSerializer
        return LotSerializer
    
    @action(detail=False, methods=['post'])
    def reorder(self, request):
        """
        Réorganise l'ordre des lots d'un devis.
        """
        devis_id = request.data.get('devis_id')
        lot_ids = request.data.get('lot_ids', [])
        
        if not devis_id:
            return Response(
                {"detail": "L'ID du devis est requis"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not lot_ids:
            return Response(
                {"detail": "La liste des IDs de lots est requise"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            devis = Devis.objects.get(pk=devis_id)
        except Devis.DoesNotExist:
            return Response(
                {"detail": "Devis non trouvé"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Vérifier que tous les lots appartiennent au devis
        lots = Lot.objects.filter(id__in=lot_ids, devis=devis)
        if len(lots) != len(lot_ids):
            return Response(
                {"detail": "Certains lots n'appartiennent pas au devis spécifié"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Mettre à jour l'ordre des lots
        for i, lot_id in enumerate(lot_ids):
            lot = lots.get(id=lot_id)
            lot.ordre = i
            lot.save()
        
        # Retourner les lots mis à jour
        serializer = LotSerializer(lots, many=True)
        return Response(serializer.data)

class LigneDevisViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour gérer les opérations CRUD sur les lignes de devis.
    
    list: Récupère toutes les lignes de devis
    retrieve: Récupère une ligne de devis par son ID
    create: Crée une nouvelle ligne de devis
    update: Met à jour une ligne de devis existante
    partial_update: Met à jour partiellement une ligne de devis
    destroy: Supprime une ligne de devis
    """
    queryset = LigneDevis.objects.all()
    serializer_class = LigneDevisSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['lot', 'type', 'ouvrage']
    ordering_fields = ['ordre', 'description']
    ordering = ['ordre']
    
    def get_serializer_class(self):
        """
        Utilise le sérialiseur approprié en fonction de l'action.
        """
        if self.action == 'retrieve':
            return LigneDevisDetailSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return LigneDevisCreateSerializer
        return LigneDevisSerializer
    
    def create(self, request, *args, **kwargs):
        """
        Surcharge de la méthode create pour gérer le cas où le type est 'ouvrage'.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Si le type est 'ouvrage', on récupère les informations de l'ouvrage
        if serializer.validated_data.get('type') == 'ouvrage':
            ouvrage_id = serializer.validated_data.get('ouvrage').id
            try:
                ouvrage = Ouvrage.objects.get(pk=ouvrage_id)
                
                # Si certains champs ne sont pas fournis, on les initialise avec les valeurs de l'ouvrage
                if not serializer.validated_data.get('description'):
                    serializer.validated_data['description'] = ouvrage.nom
                
                if not serializer.validated_data.get('unite'):
                    serializer.validated_data['unite'] = ouvrage.unite
                
                if not serializer.validated_data.get('debourse'):
                    serializer.validated_data['debourse'] = ouvrage.debourse_sec
                
                # Si le prix unitaire n'est pas fourni, on le calcule avec une marge de 30%
                if not serializer.validated_data.get('prix_unitaire'):
                    debourse = ouvrage.debourse_sec
                    if debourse > 0:
                        serializer.validated_data['prix_unitaire'] = debourse / 0.7  # Marge de 30%
                    else:
                        serializer.validated_data['prix_unitaire'] = 0
            
            except Ouvrage.DoesNotExist:
                pass  # Si l'ouvrage n'existe pas, on ne fait rien de spécial
        
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    @action(detail=False, methods=['post'])
    def reorder(self, request):
        """
        Réorganise l'ordre des lignes d'un lot.
        """
        lot_id = request.data.get('lot_id')
        ligne_ids = request.data.get('ligne_ids', [])
        
        if not lot_id:
            return Response(
                {"detail": "L'ID du lot est requis"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not ligne_ids:
            return Response(
                {"detail": "La liste des IDs de lignes est requise"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            lot = Lot.objects.get(pk=lot_id)
        except Lot.DoesNotExist:
            return Response(
                {"detail": "Lot non trouvé"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Vérifier que toutes les lignes appartiennent au lot
        lignes = LigneDevis.objects.filter(id__in=ligne_ids, lot=lot)
        if len(lignes) != len(ligne_ids):
            return Response(
                {"detail": "Certaines lignes n'appartiennent pas au lot spécifié"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Mettre à jour l'ordre des lignes
        for i, ligne_id in enumerate(ligne_ids):
            ligne = lignes.get(id=ligne_id)
            ligne.ordre = i
            ligne.save()
        
        # Retourner les lignes mises à jour
        serializer = LigneDevisSerializer(lignes, many=True)
        return Response(serializer.data)
