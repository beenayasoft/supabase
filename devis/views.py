from django.shortcuts import render, get_object_or_404
from django.db.models import Sum, Avg, Count
from rest_framework import viewsets, status, filters, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Devis, Lot, LigneDevis
from .serializers import (
    DevisSerializer, DevisDetailSerializer, DevisCreateSerializer,
    LotSerializer, LotDetailSerializer,
    LigneDevisSerializer, LigneDevisDetailSerializer, LigneDevisCreateSerializer,
    DevisFromOpportunitySerializer
)
from bibliotheque.models import Ouvrage
from decimal import Decimal, ROUND_HALF_UP
from opportunite.models import Opportunity

class DevisViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour gérer les opérations CRUD sur les devis.
    
    list: Récupère tous les devis
    retrieve: Récupère un devis par son ID
    create: Crée un nouveau devis
    update: Met à jour un devis existant
    partial_update: Met à jour partiellement un devis
    destroy: Supprime un devis
    
    Endpoints additionnels:
    - calculations: Retourne les calculs détaillés pour un devis spécifique
    - stats: Retourne des statistiques globales sur les devis
    - from_opportunity: Crée un devis à partir d'une opportunité
    """
    queryset = Devis.objects.all()
    serializer_class = DevisSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['client', 'statut', 'opportunity']
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
        elif self.action == 'from_opportunity':
            return DevisFromOpportunitySerializer
        return DevisSerializer
    
    @action(detail=False, methods=['post'])
    def from_opportunity(self, request):
        """
        Crée un devis à partir d'une opportunité.
        
        Paramètres requis:
        - opportunity_id: UUID de l'opportunité
        - numero: Numéro du devis à créer
        
        Paramètres optionnels:
        - date_validite: Date de validité du devis
        - commentaire: Commentaire pour le devis
        - conditions_paiement: Conditions de paiement
        - marge_globale: Marge globale en pourcentage
        """
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            # Créer le devis
            devis = serializer.save()
            
            # Retourner le devis créé
            return Response(
                DevisDetailSerializer(devis, context={'request': request}).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
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
            marge_globale=devis.marge_globale,
            opportunity=devis.opportunity
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
        
        Paramètres de requête:
        - show_costs (bool): Affiche ou non les informations de coûts et marges (par défaut: false)
                            L'affichage est soumis aux autorisations de l'utilisateur.
        """
        from django.http import HttpResponse
        from .pdf_generator import DevisPDFGenerator
        import os
        
        devis = self.get_object()
        
        # Vérifier si l'utilisateur veut voir les coûts et s'il en a le droit
        show_costs_param = request.query_params.get('show_costs', 'false').lower() == 'true'
        show_costs = show_costs_param and self.user_can_view_costs(request.user)
        
        # Générer le PDF
        pdf_generator = DevisPDFGenerator(devis, show_costs=show_costs)
        pdf_buffer = pdf_generator.generate_pdf()
        
        # Créer la réponse HTTP avec le PDF
        filename = f"devis_{devis.numero}.pdf".replace('/', '-').replace(' ', '_')
        response = HttpResponse(pdf_buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response
        
    @action(detail=True, methods=['get'])
    def calculations(self, request, pk=None):
        """
        Retourne les calculs détaillés pour un devis : totaux par lot, totaux globaux, marges.
        L'accès aux informations de coûts et marges est filtré selon le rôle de l'utilisateur.
        """
        devis = self.get_object()
        
        # Vérifier si l'utilisateur a le droit de voir les données de coûts
        show_costs = self.user_can_view_costs(request.user)
        
        # Préparer les données de base du devis
        result = {
            "id": devis.id,
            "numero": devis.numero,
            "client": devis.client.nom,
            "objet": devis.objet,
            "statut": devis.statut,
            "total_ht": devis.total_ht
        }
        
        # Ajouter les informations de coûts si l'utilisateur est autorisé
        if show_costs:
            result.update({
                "total_debourse": devis.total_debourse,
                "marge_totale": devis.marge_totale
            })
        
        # Préparer les détails par lot
        lots_data = []
        for lot in devis.lots.all().order_by('ordre'):
            lot_data = {
                "id": lot.id,
                "nom": lot.nom,
                "total_ht": lot.total_ht
            }
            
            # Ajouter les informations de coûts des lots si l'utilisateur est autorisé
            if show_costs:
                lot_data.update({
                    "total_debourse": lot.total_debourse,
                    "marge": lot.marge
                })
            
            # Ajouter les détails des lignes
            lignes_data = []
            for ligne in lot.lignes.all().order_by('ordre'):
                ligne_data = {
                    "id": ligne.id,
                    "description": ligne.description,
                    "quantite": ligne.quantite,
                    "unite": ligne.unite,
                    "prix_unitaire": ligne.prix_unitaire,
                    "total_ht": ligne.total_ht
                }
                
                # Ajouter les informations de coûts des lignes si l'utilisateur est autorisé
                if show_costs:
                    ligne_data.update({
                        "debourse": ligne.debourse,
                        "total_debourse": ligne.total_debourse,
                        "marge": ligne.marge
                    })
                
                lignes_data.append(ligne_data)
            
            lot_data["lignes"] = lignes_data
            lots_data.append(lot_data)
        
        result["lots"] = lots_data
        
        # Retourner le résultat complet
        return Response(result)
    
    def user_can_view_costs(self, user):
        """
        Détermine si un utilisateur peut voir les informations de coûts et marges.
        Actuellement, tous les utilisateurs authentifiés peuvent les voir.
        Dans une implémentation réelle, il faudrait vérifier les rôles/permissions.
        """
        # TODO: Implémenter la vérification basée sur les rôles quand l'authentification sera en place
        # Pour l'instant, on suppose que c'est accessible à tous les utilisateurs authentifiés
        return user.is_authenticated
        
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        Retourne des statistiques globales sur les devis.
        L'accès est filtré selon les rôles.
        """
        # Vérifier si l'utilisateur a le droit de voir les données de coûts
        show_costs = self.user_can_view_costs(request.user)
        
        # Statistiques de base accessibles à tous
        basic_stats = {
            "total_devis": Devis.objects.count(),
            "devis_par_statut": {
                status: Devis.objects.filter(statut=status).count()
                for status, _ in Devis.STATUT_CHOICES
            },
            "montant_total_ht": Devis.objects.aggregate(total=Sum('total_ht'))['total'] or 0,
        }
        
        # Statistiques incluant les informations de coûts (réservées aux rôles autorisés)
        cost_stats = {}
        if show_costs:
            # Récupérer les données de coûts et de marges
            margin_data = Devis.objects.aggregate(
                debourse_total=Sum('total_debourse'),
                marge_moyenne=Avg('marge_totale')
            )
            
            cost_stats = {
                "debourse_total": margin_data['debourse_total'] or 0,
                "marge_moyenne": margin_data['marge_moyenne'] or 0,
                # Répartition de marge par statut (pour analyse)
                "marges_par_statut": {
                    status: Devis.objects.filter(statut=status).aggregate(
                        avg_margin=Avg('marge_totale')
                    )['avg_margin'] or 0
                    for status, _ in Devis.STATUT_CHOICES
                }
            }
        
        # Combiner les statistiques
        result = {**basic_stats}
        if cost_stats:
            result.update(cost_stats)
        
        return Response(result)

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
        Cette version vérifie et remplit les données AVANT la validation du sérialiseur.
        """
        # Récupérer les données de la requête
        request_data = request.data.copy()
        
        # Vérifier si c'est une ligne de type 'ouvrage'
        if request_data.get('type') == 'ouvrage' and request_data.get('ouvrage'):
            try:
                # Récupérer l'ouvrage avant la validation
                ouvrage_id = request_data.get('ouvrage')
                ouvrage = Ouvrage.objects.get(pk=ouvrage_id)
                
                # Pré-remplir les champs manquants avec les valeurs de l'ouvrage
                if not request_data.get('description'):
                    request_data['description'] = ouvrage.nom
                
                if not request_data.get('unite'):
                    request_data['unite'] = ouvrage.unite
                
                if not request_data.get('debourse'):
                    # On arrondit à 2 décimales maximum
                    request_data['debourse'] = str(round(ouvrage.debourse_sec, 2))  # Conversion en string pour JSON
                
                # Si le prix unitaire n'est pas fourni, on le calcule avec une marge de 30%
                if not request_data.get('prix_unitaire'):
                    from decimal import Decimal, ROUND_HALF_UP
                    debourse = ouvrage.debourse_sec
                    if debourse > 0:
                        # Utilisation de Decimal pour éviter l'erreur de type
                        # On arrondit à 2 décimales et on s'assure de ne pas dépasser 10 chiffres au total
                        prix = (debourse / Decimal('0.7')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                        # Vérifier que le nombre ne dépasse pas 10 chiffres au total
                        # Si c'est le cas, on le tronque à 9999999.99
                        if len(str(prix).replace('.', '')) > 10:
                            prix = Decimal('9999999.99')
                        request_data['prix_unitaire'] = str(prix)
                    else:
                        request_data['prix_unitaire'] = '0'
                        
            except Ouvrage.DoesNotExist:
                # Si l'ouvrage n'existe pas, on retourne une erreur claire
                return Response(
                    {"ouvrage": [f"L'ouvrage avec l'ID {ouvrage_id} n'existe pas."]},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Maintenant on valide le sérialiseur avec les données complétées
        serializer = self.get_serializer(data=request_data)
        serializer.is_valid(raise_exception=True)
        
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


class DevisLineViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour gérer les opérations CRUD sur les lignes de devis avec routes imbriquées.
    
    URLs imbriquées:
    - POST /api/quotes/devis/{devis_pk}/lines/
    - GET /api/quotes/devis/{devis_pk}/lines/
    - GET /api/quotes/devis/{devis_pk}/lines/{pk}/
    - PUT /api/quotes/devis/{devis_pk}/lines/{pk}/
    - DELETE /api/quotes/devis/{devis_pk}/lines/{pk}/
    - POST /api/quotes/devis/{devis_pk}/lines/reorder/
    """
    serializer_class = LigneDevisSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    ordering_fields = ['ordre', 'description']
    ordering = ['ordre']
    
    def get_queryset(self):
        """
        Retourne les lignes appartenant au devis spécifié dans l'URL.
        """
        devis_id = self.kwargs['devis_pk']
        # Vérifier que le devis existe
        get_object_or_404(Devis, pk=devis_id)
        # Retourner les lignes des lots associés à ce devis
        return LigneDevis.objects.filter(lot__devis=devis_id)
    
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
        Cette version vérifie et remplit les données AVANT la validation du sérialiseur.
        """
        # Récupérer les données de la requête
        request_data = request.data.copy()
        
        # Vérifier si c'est une ligne de type 'ouvrage'
        if request_data.get('type') == 'ouvrage' and request_data.get('ouvrage'):
            try:
                # Récupérer l'ouvrage avant la validation
                ouvrage_id = request_data.get('ouvrage')
                ouvrage = Ouvrage.objects.get(pk=ouvrage_id)
                
                # Pré-remplir les champs manquants avec les valeurs de l'ouvrage
                if not request_data.get('description'):
                    request_data['description'] = ouvrage.nom
                
                if not request_data.get('unite'):
                    request_data['unite'] = ouvrage.unite
                
                # On arrondit le déboursé à 2 décimales maximum
                if not request_data.get('debourse'):
                    request_data['debourse'] = str(round(ouvrage.debourse_sec, 2))  # Conversion en string pour JSON
                
                # Si le prix unitaire n'est pas fourni, on le calcule avec une marge de 30%
                if not request_data.get('prix_unitaire'):
                    from decimal import Decimal, ROUND_HALF_UP
                    debourse = ouvrage.debourse_sec
                    if debourse > 0:
                        # On arrondit à 2 décimales et on s'assure de ne pas dépasser 10 chiffres au total
                        prix = (debourse / Decimal('0.7')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                        # Vérifier que le nombre ne dépasse pas 10 chiffres au total
                        if len(str(prix).replace('.', '')) > 10:
                            prix = Decimal('9999999.99')
                        request_data['prix_unitaire'] = str(prix)
                    else:
                        request_data['prix_unitaire'] = '0'
                        
            except Ouvrage.DoesNotExist:
                # Si l'ouvrage n'existe pas, on retourne une erreur claire
                return Response(
                    {"ouvrage": [f"L'ouvrage avec l'ID {ouvrage_id} n'existe pas."]},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Maintenant on valide le sérialiseur avec les données complétées
        serializer = self.get_serializer(data=request_data)
        serializer.is_valid(raise_exception=True)
        
        # Vérification du lot
        devis_id = self.kwargs['devis_pk']
        lot_id = serializer.validated_data.get('lot').id
        
        # Vérifier que le lot existe et appartient au devis spécifié
        lot = get_object_or_404(Lot, pk=lot_id)
        if str(lot.devis.id) != devis_id:
            raise serializers.ValidationError({
                'lot': [f"Le lot avec l'ID {lot_id} n'appartient pas au devis avec l'ID {devis_id}."]
            })
        
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    def perform_create(self, serializer):
        """
        Enregistre la nouvelle ligne.
        """
        serializer.save()
    
    @action(detail=False, methods=['post'])
    def reorder(self, request, devis_pk=None):
        """
        Réorganise l'ordre des lignes dans un devis.
        """
        devis_id = devis_pk
        ligne_ids = request.data.get('ligne_ids', [])
        lot_id = request.data.get('lot_id')
        
        if not ligne_ids:
            return Response(
                {"detail": "La liste des IDs de lignes est requise"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        if not lot_id:
            return Response(
                {"detail": "L'ID du lot est requis"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            lot = Lot.objects.get(pk=lot_id, devis=devis_id)
        except Lot.DoesNotExist:
            return Response(
                {"detail": f"Le lot avec l'ID {lot_id} n'appartient pas au devis avec l'ID {devis_id}"}, 
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
