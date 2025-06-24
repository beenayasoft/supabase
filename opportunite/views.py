from django.shortcuts import render
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Sum, Count, F, ExpressionWrapper, DecimalField, Avg, Case, When, Value, IntegerField, Func, Min, Max
from django.utils import timezone
import uuid
from datetime import timedelta

from .models import Opportunity, OpportunityStatus, OpportunitySource, LossReason
from .serializers import (
    OpportunityListSerializer,
    OpportunityDetailSerializer,
    OpportunityCreateUpdateSerializer,
    OpportunityPatchSerializer
)
from .filters import OpportunityFilter


class OpportunityViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour gérer les opportunités commerciales (prospects, deals, etc.)
    
    Fonctionnalités:
    - Liste, détail, création, mise à jour et suppression des opportunités
    - Filtres avancés par étape, montant, dates, etc.
    - Mise à jour partielle pour les changements d'étape (kanban)
    - Vue tableau de bord avec KPIs commerciaux
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = OpportunityFilter
    search_fields = ['name', 'description', 'tier__nom']
    ordering_fields = ['name', 'created_at', 'expected_close_date', 'estimated_amount', 'probability']
    ordering = ['-created_at']

    def get_queryset(self):
        """Retourne toutes les opportunités, avec possibilité de filtres supplémentaires"""
        # Base queryset avec optimisation des requêtes
        queryset = Opportunity.objects.select_related('tier')
        
        # Pour les actions qui nécessitent les détails complets du tier
        if self.action in ['retrieve', 'dashboard', 'pipeline']:
            queryset = queryset.prefetch_related(
                'tier__adresses',
                'tier__contacts'
            )
        
        # Filtre pour les opportunités par étape
        stage = self.request.query_params.get('stage')
        if stage:
            if ',' in stage:
                # Support pour filtrage multi-étapes
                stages = stage.split(',')
                queryset = queryset.filter(stage__in=stages)
            else:
                queryset = queryset.filter(stage=stage)
        
        # Filtre pour les opportunités par période
        period = self.request.query_params.get('period')
        if period:
            today = timezone.now().date()
            if period == 'this_month':
                queryset = queryset.filter(
                    created_at__year=today.year,
                    created_at__month=today.month
                )
            elif period == 'this_quarter':
                quarter_start_month = ((today.month - 1) // 3) * 3 + 1
                queryset = queryset.filter(
                    created_at__year=today.year,
                    created_at__month__gte=quarter_start_month,
                    created_at__month__lte=quarter_start_month + 2
                )
            elif period == 'this_year':
                queryset = queryset.filter(created_at__year=today.year)
            elif period == 'last_30_days':
                queryset = queryset.filter(
                    created_at__gte=today - timezone.timedelta(days=30)
                )
        
        return queryset

    def get_serializer_class(self):
        """Sélectionne le serializer approprié selon l'action"""
        if self.action == 'list':
            return OpportunityListSerializer
        elif self.action == 'retrieve':
            return OpportunityDetailSerializer
        elif self.action in ['partial_update', 'change_stage']:
            return OpportunityPatchSerializer
        elif self.action in ['create', 'update']:
            return OpportunityCreateUpdateSerializer
        return OpportunityListSerializer
        
    def perform_create(self, serializer):
        """Associer automatiquement l'utilisateur actuel à l'opportunité si non spécifié"""
        if not serializer.validated_data.get('assigned_to'):
            serializer.save(assigned_to=self.request.user.email)
        else:
            serializer.save()

    @action(detail=True, methods=['post'])
    def generate_quote(self, request, pk=None):
        """
        Génère un devis à partir d'une opportunité.
        
        Cette action crée un nouveau devis basé sur les informations de l'opportunité.
        Le devis est créé avec un lot par défaut, sans lignes.
        """
        from devis.models import Devis, Lot
        from devis.serializers import DevisDetailSerializer
        
        opportunity = self.get_object()
        
        # Générer un numéro de devis unique
        current_date = timezone.now().strftime('%Y%m%d')
        numero_devis = f"D-{current_date}-{str(uuid.uuid4())[:8]}"
        
        # Créer le devis
        devis = Devis.objects.create(
            client=opportunity.tier,
            objet=f"Devis pour {opportunity.name}",
            statut='brouillon',
            numero=numero_devis,
            opportunity=opportunity
        )
        
        # Créer un lot par défaut
        Lot.objects.create(
            devis=devis,
            nom="Prestations",
            ordre=1,
            description=f"Prestations pour {opportunity.name}"
        )
        
        # Retourner le devis créé
        serializer = DevisDetailSerializer(devis, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['patch'])
    def change_stage(self, request, pk=None):
        """
        Endpoint spécialisé pour changer l'étape d'une opportunité (pour le kanban).
        Cette méthode est optimisée pour le drag & drop dans l'interface kanban.
        """
        opportunity = self.get_object()
        
        # Utiliser le serializer pour valider et mettre à jour
        serializer = self.get_serializer(opportunity, data=request.data, partial=True)
        if serializer.is_valid():
            # Si l'étape change vers "won" ou "lost", enregistrer la date de clôture
            if 'stage' in serializer.validated_data:
                new_stage = serializer.validated_data['stage']
                if new_stage in [OpportunityStatus.WON, OpportunityStatus.LOST] and not opportunity.closed_at:
                    serializer.save(closed_at=timezone.now())
                else:
                    serializer.save()
            else:
                serializer.save()
                
            # Retourner l'opportunité mise à jour avec les détails complets
            return Response(OpportunityDetailSerializer(
                opportunity, 
                context={'request': request}
            ).data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def pipeline(self, request):
        """
        Endpoint spécial pour afficher le pipeline commercial (kanban)
        Retourne les opportunités groupées par étape
        """
        # Utiliser le queryset filtré avec les optimisations
        queryset = self.filter_queryset(self.get_queryset())
        
        # Structure pour le pipeline
        pipeline = {}
        
        # Initialiser toutes les étapes
        for stage_code, stage_name in OpportunityStatus.choices:
            pipeline[stage_code] = {
                'name': stage_name,
                'opportunities': [],
                'total_amount': 0,
                'count': 0,
                'weighted_amount': 0
            }
        
        # Optimisation: Calculer les totaux par étape en une seule requête SQL
        stage_totals = (
            queryset
            .values('stage')
            .annotate(
                total_amount=Sum('estimated_amount'),
                count=Count('id'),
                weighted_amount=Sum(
                    ExpressionWrapper(
                        F('estimated_amount') * F('probability') / 100,
                        output_field=DecimalField()
                    )
                )
            )
        )
        
        # Mettre à jour les totaux pour chaque étape
        for total in stage_totals:
            stage = total['stage']
            pipeline[stage]['total_amount'] = float(total['total_amount'] or 0)
            pipeline[stage]['count'] = total['count']
            pipeline[stage]['weighted_amount'] = float(total['weighted_amount'] or 0)
        
        # Optimisation: Récupérer les opportunités avec les données nécessaires uniquement
        # et les organiser par étape
        opportunities = (
            queryset
            .select_related('tier')
            .only('id', 'name', 'stage', 'estimated_amount', 'probability', 'expected_close_date', 'tier__nom')
        )
        
        # Organiser les opportunités par étape
        for opp in opportunities:
            serializer = OpportunityListSerializer(opp, context={'request': request})
            pipeline[opp.stage]['opportunities'].append(serializer.data)
        
        return Response(pipeline)
        
    @action(detail=False, methods=['post'])
    def move_opportunity(self, request):
        """
        Endpoint pour déplacer une opportunité d'une étape à une autre
        Utilisé pour les opérations de drag & drop dans l'interface kanban
        """
        opportunity_id = request.data.get('opportunity_id')
        new_stage = request.data.get('stage')
        
        if not opportunity_id or not new_stage:
            return Response(
                {'error': 'opportunity_id et stage sont requis'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Vérifier que l'étape est valide avant de faire la requête à la base de données
        if new_stage not in dict(OpportunityStatus.choices):
            return Response(
                {'error': 'Étape invalide'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            # Optimisation: Utiliser select_for_update pour éviter les problèmes de concurrence
            # et sélectionner uniquement les champs nécessaires
            opportunity = (
                Opportunity.objects
                .select_related('tier')
                .only('id', 'name', 'stage', 'closed_at', 'tier__id', 'tier__nom')
                .get(pk=opportunity_id)
            )
        except Opportunity.DoesNotExist:
            return Response(
                {'error': 'Opportunité non trouvée'}, 
                status=status.HTTP_404_NOT_FOUND
            )
            
        # Mettre à jour l'étape
        old_stage = opportunity.stage
        opportunity.stage = new_stage
        
        # Si l'opportunité passe à "won" ou "lost", enregistrer la date de clôture
        if new_stage in [OpportunityStatus.WON, OpportunityStatus.LOST] and not opportunity.closed_at:
            opportunity.closed_at = timezone.now()
            
        # Optimisation: Mettre à jour uniquement les champs modifiés
        update_fields = ['stage']
        if new_stage in [OpportunityStatus.WON, OpportunityStatus.LOST] and not opportunity.closed_at:
            update_fields.append('closed_at')
            
        opportunity.save(update_fields=update_fields)
        
        # Retourner l'opportunité mise à jour avec plus de détails
        serializer = OpportunityListSerializer(opportunity, context={'request': request})
        return Response({
            'opportunity': serializer.data,
            'old_stage': old_stage,
            'new_stage': new_stage,
            'success': True
        })

    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """
        Endpoint pour les KPIs du tableau de bord commercial
        
        Fournit des indicateurs clés de performance (KPIs) pour analyser l'activité commerciale:
        - Statistiques globales (montants, nombre d'opportunités)
        - Statistiques par étape du pipeline
        - Taux de conversion entre les étapes
        - Analyse par période (mois, trimestre, année)
        - Analyse des pertes et raisons
        - Performance par source d'opportunité
        - Durée moyenne du cycle de vente
        """
        # Obtenir le queryset filtré (si des filtres sont appliqués)
        queryset = self.filter_queryset(self.get_queryset())
        
        # Définir les périodes pour l'analyse temporelle
        today = timezone.now().date()
        this_month_start = today.replace(day=1)
        this_quarter_start = today.replace(month=((today.month - 1) // 3) * 3 + 1, day=1)
        this_year_start = today.replace(month=1, day=1)
        
        # 1. STATISTIQUES PAR ÉTAPE
        # -------------------------
        stage_stats = (
            queryset
            .values('stage')
            .annotate(
                count=Count('id'),
                total_amount=Sum('estimated_amount'),
                weighted_amount=Sum(
                    ExpressionWrapper(
                        F('estimated_amount') * F('probability') / 100,
                        output_field=DecimalField()
                    )
                )
            )
        )
        
        # Convertir en dict pour accès facile
        stage_data = {
            item['stage']: {
                'count': item['count'],
                'total_amount': float(item['total_amount']) if item['total_amount'] else 0,
                'weighted_amount': float(item['weighted_amount']) if item['weighted_amount'] else 0
            }
            for item in stage_stats
        }
        
        # 2. TOTAUX GLOBAUX
        # ----------------
        total_amount = sum(item['total_amount'] or 0 for item in stage_stats)
        total_weighted = sum(item['weighted_amount'] or 0 for item in stage_stats)
        total_count = sum(item['count'] for item in stage_stats)
        
        # 3. TAUX DE CONVERSION
        # -------------------
        conversion_rates = {}
        stages = dict(OpportunityStatus.choices)
        
        # Conversion de qualification à négociation
        if stage_data.get(OpportunityStatus.NEEDS_ANALYSIS, {}).get('count', 0) > 0:
            qualification_to_negotiation = (
                stage_data.get(OpportunityStatus.NEGOTIATION, {}).get('count', 0) /
                stage_data.get(OpportunityStatus.NEEDS_ANALYSIS, {}).get('count', 1)
            ) * 100
            conversion_rates['qualification_to_negotiation'] = round(qualification_to_negotiation, 1)
        
        # Conversion de négociation à gagnée
        if stage_data.get(OpportunityStatus.NEGOTIATION, {}).get('count', 0) > 0:
            negotiation_to_won = (
                stage_data.get(OpportunityStatus.WON, {}).get('count', 0) /
                stage_data.get(OpportunityStatus.NEGOTIATION, {}).get('count', 1)
            ) * 100
            conversion_rates['negotiation_to_won'] = round(negotiation_to_won, 1)
        
        # Taux de conversion global
        if (stage_data.get(OpportunityStatus.NEEDS_ANALYSIS, {}).get('count', 0) +
                stage_data.get(OpportunityStatus.NEW, {}).get('count', 0)) > 0:
            global_conversion = (
                stage_data.get(OpportunityStatus.WON, {}).get('count', 0) /
                (stage_data.get(OpportunityStatus.NEEDS_ANALYSIS, {}).get('count', 0) +
                 stage_data.get(OpportunityStatus.NEW, {}).get('count', 0))
            ) * 100
            conversion_rates['global'] = round(global_conversion, 1)
        
        # 4. STATISTIQUES PAR PÉRIODE
        # -------------------------
        # Cette année
        year_stats = self._get_period_stats(
            queryset.filter(created_at__gte=this_year_start)
        )
        
        # Ce trimestre
        quarter_stats = self._get_period_stats(
            queryset.filter(created_at__gte=this_quarter_start)
        )
        
        # Ce mois
        month_stats = self._get_period_stats(
            queryset.filter(created_at__gte=this_month_start)
        )
        
        # 30 derniers jours
        last_30_days_stats = self._get_period_stats(
            queryset.filter(created_at__gte=today - timedelta(days=30))
        )
        
        # 5. ANALYSE DES PERTES
        # -------------------
        loss_stats = (
            queryset
            .filter(stage=OpportunityStatus.LOST)
            .values('loss_reason')
            .annotate(
                count=Count('id'),
                total_amount=Sum('estimated_amount')
            )
            .order_by('-count')
        )
        
        loss_reasons = dict(LossReason.choices)
        loss_data = {}
        for item in loss_stats:
            if item['loss_reason']:
                # Convertir la clé __proxy__ en chaîne de caractères
                reason_key = str(loss_reasons.get(item['loss_reason'], 'Non spécifié'))
                loss_data[reason_key] = {
                    'count': item['count'],
                    'total_amount': float(item['total_amount']) if item['total_amount'] else 0,
                    'percentage': round((item['count'] / max(stage_data.get(OpportunityStatus.LOST, {}).get('count', 1), 1)) * 100, 1)
                }
        
        # 6. PERFORMANCE PAR SOURCE
        # -----------------------
        source_stats = (
            queryset
            .values('source')
            .annotate(
                count=Count('id'),
                total_amount=Sum('estimated_amount'),
                won_count=Count(Case(When(stage=OpportunityStatus.WON, then=1))),
                lost_count=Count(Case(When(stage=OpportunityStatus.LOST, then=1)))
            )
            .order_by('-count')
        )
        
        sources = dict(OpportunitySource.choices)
        source_data = {}
        for item in source_stats:
            # Convertir la clé __proxy__ en chaîne de caractères
            source_key = str(sources.get(item['source'], 'Non spécifié'))
            source_data[source_key] = {
                'count': item['count'],
                'total_amount': float(item['total_amount']) if item['total_amount'] else 0,
                'won_count': item['won_count'],
                'lost_count': item['lost_count'],
                'win_rate': round((item['won_count'] / max(item['won_count'] + item['lost_count'], 1)) * 100, 1)
            }
        
        # 7. DURÉE MOYENNE DU CYCLE DE VENTE
        # --------------------------------
        # Calculer pour les opportunités gagnées qui ont une date de clôture
        sales_cycle = queryset.filter(
            stage=OpportunityStatus.WON,
            closed_at__isnull=False
        ).annotate(
            cycle_days=ExpressionWrapper(
                F('closed_at') - F('created_at'),
                output_field=IntegerField()
            )
        ).aggregate(
            avg_cycle=Avg('cycle_days'),
            min_cycle=Min('cycle_days'),
            max_cycle=Max('cycle_days')
        )
        
        # Construire la réponse
        by_stage = {}
        for stage_code, stage_name in OpportunityStatus.choices:
            # Convertir la clé __proxy__ en chaîne de caractères
            stage_key = str(stage_code)
            if stage_key in stage_data:
                by_stage[stage_key] = {
                    'name': str(stage_name),
                    'count': stage_data[stage_key].get('count', 0),
                    'total_amount': stage_data[stage_key].get('total_amount', 0),
                    'weighted_amount': stage_data[stage_key].get('weighted_amount', 0)
                }
            else:
                by_stage[stage_key] = {
                    'name': str(stage_name),
                    'count': 0,
                    'total_amount': 0,
                    'weighted_amount': 0
                }
        
        response = {
            'summary': {
                'total_amount': total_amount,
                'total_weighted_amount': total_weighted,
                'total_count': total_count,
                'conversion_rates': conversion_rates,
                'avg_sales_cycle_days': sales_cycle['avg_cycle'],
                'min_sales_cycle_days': sales_cycle['min_cycle'],
                'max_sales_cycle_days': sales_cycle['max_cycle']
            },
            'by_stage': by_stage,
            'by_period': {
                'this_year': year_stats,
                'this_quarter': quarter_stats,
                'this_month': month_stats,
                'last_30_days': last_30_days_stats
            },
            'by_loss_reason': loss_data,
            'by_source': source_data
        }
        
        return Response(response)
    
    def _get_period_stats(self, queryset):
        """
        Méthode utilitaire pour calculer les statistiques sur une période donnée
        """
        stats = queryset.aggregate(
            count=Count('id'),
            total_amount=Sum('estimated_amount'),
            won_count=Count(Case(When(stage=OpportunityStatus.WON, then=1))),
            lost_count=Count(Case(When(stage=OpportunityStatus.LOST, then=1))),
            weighted_amount=Sum(
                ExpressionWrapper(
                    F('estimated_amount') * F('probability') / 100,
                    output_field=DecimalField()
                )
            )
        )
        
        # Calculer le taux de succès
        total_closed = stats['won_count'] + stats['lost_count']
        win_rate = (stats['won_count'] / max(total_closed, 1)) * 100 if total_closed > 0 else 0
        
        return {
            'count': stats['count'],
            'total_amount': float(stats['total_amount']) if stats['total_amount'] else 0,
            'weighted_amount': float(stats['weighted_amount']) if stats['weighted_amount'] else 0,
            'won_count': stats['won_count'],
            'lost_count': stats['lost_count'],
            'win_rate': round(win_rate, 1)
        }
