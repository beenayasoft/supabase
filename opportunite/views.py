from django.shortcuts import render
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.shortcuts import get_object_or_404

from .models import Opportunity, OpportunityStatus
from .serializers import (
    OpportunitySerializer, 
    OpportunityListSerializer,
    OpportunityKanbanSerializer,
    OpportunityStageUpdateSerializer,
    OpportunityCreateQuoteSerializer
)
from tiers.models import Tiers
from devis.models import Quote


class OpportunityViewSet(viewsets.ModelViewSet):
    """ViewSet complet pour la gestion des opportunités avec actions métier"""
    
    queryset = Opportunity.objects.select_related('tier').order_by('-created_at')
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['stage', 'source', 'tier', 'assigned_to']
    search_fields = ['name', 'description', 'tier__nom', 'tier__email']
    ordering_fields = ['created_at', 'updated_at', 'expected_close_date', 'estimated_amount', 'probability']
    ordering = ['-created_at']

    def get_serializer_class(self):
        """Sélectionne le serializer approprié selon l'action"""
        if self.action == 'list':
            return OpportunityListSerializer
        elif self.action == 'kanban':
            return OpportunityKanbanSerializer
        elif self.action in ['update_stage', 'mark_won', 'mark_lost']:
            return OpportunityStageUpdateSerializer
        elif self.action == 'create_quote':
            return OpportunityCreateQuoteSerializer
        return OpportunitySerializer

    def perform_create(self, serializer):
        """Logique métier lors de la création"""
        serializer.save()

    def perform_update(self, serializer):
        """Logique métier lors de la mise à jour"""
        serializer.save()

    @action(detail=False, methods=['get'])
    def kanban(self, request):
        """Vue spéciale pour l'interface Kanban"""
        opportunities = self.get_queryset()
        
        # Organiser par statut pour le Kanban
        kanban_data = {}
        for stage_choice in OpportunityStatus.choices:
            stage_code, stage_label = stage_choice
            stage_opportunities = opportunities.filter(stage=stage_code)
            kanban_data[stage_code] = {
                'label': stage_label,
                'count': stage_opportunities.count(),
                'opportunities': OpportunityKanbanSerializer(stage_opportunities, many=True).data
            }
        
        return Response(kanban_data)

    @action(detail=True, methods=['patch'])
    def update_stage(self, request, pk=None):
        """Mise à jour du statut avec validation métier"""
        opportunity = self.get_object()
        serializer = OpportunityStageUpdateSerializer(
            opportunity, 
            data=request.data, 
            partial=True
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response(OpportunitySerializer(opportunity).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def mark_won(self, request, pk=None):
        """Marquer une opportunité comme gagnée"""
        opportunity = self.get_object()
        
        if opportunity.stage == OpportunityStatus.WON:
            return Response(
                {'detail': 'Cette opportunité est déjà marquée comme gagnée.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Générer un ID de projet si pas fourni
        project_id = request.data.get('project_id')
        if not project_id:
            project_id = f"PROJ-{timezone.now().strftime('%Y%m%d')}-{opportunity.id.hex[:8]}"
        
        opportunity.stage = OpportunityStatus.WON
        opportunity.project_id = project_id
        opportunity.probability = 100
        opportunity.closed_at = timezone.now()
        opportunity.save()
        
        return Response({
            'detail': 'Opportunité marquée comme gagnée avec succès.',
            'project_id': project_id,
            'opportunity': OpportunitySerializer(opportunity).data
        })

    @action(detail=True, methods=['post'])
    def mark_lost(self, request, pk=None):
        """Marquer une opportunité comme perdue"""
        opportunity = self.get_object()
        
        if opportunity.stage == OpportunityStatus.LOST:
            return Response(
                {'detail': 'Cette opportunité est déjà marquée comme perdue.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        loss_reason = request.data.get('loss_reason')
        if not loss_reason:
            return Response(
                {'detail': 'La raison de perte est obligatoire.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        opportunity.stage = OpportunityStatus.LOST
        opportunity.loss_reason = loss_reason
        opportunity.loss_description = request.data.get('loss_description', '')
        opportunity.probability = 0
        opportunity.closed_at = timezone.now()
        opportunity.save()
        
        return Response({
            'detail': 'Opportunité marquée comme perdue.',
            'opportunity': OpportunitySerializer(opportunity).data
        })

    @action(detail=True, methods=['post'])
    def create_quote(self, request, pk=None):
        """Créer un devis depuis une opportunité"""
        opportunity = self.get_object()
        
        # Vérifier si l'opportunité peut générer un devis
        if opportunity.stage not in [OpportunityStatus.NEEDS_ANALYSIS, OpportunityStatus.NEGOTIATION]:
            return Response(
                {'detail': 'Un devis ne peut être créé que pour les opportunités en analyse ou négociation.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = OpportunityCreateQuoteSerializer(
            data=request.data,
            context={'opportunity': opportunity}
        )
        
        if serializer.is_valid():
            # Créer le devis
            quote_data = {
                'tier': opportunity.tier,
                'title': serializer.validated_data.get('title', f"Devis - {opportunity.name}"),
                'description': serializer.validated_data.get('description', opportunity.description or ''),
                'notes_internes': serializer.validated_data.get('notes_internes', ''),
                'total_ht': opportunity.estimated_amount,
                'total_ttc': opportunity.estimated_amount * 1.2,  # TVA par défaut 20%
                # opportunity: opportunity,  # Sera décommenté après migration
            }
            
            quote = Quote.objects.create(**quote_data)
            
            # Mettre à jour l'opportunité vers négociation si en analyse
            if opportunity.stage == OpportunityStatus.NEEDS_ANALYSIS:
                opportunity.stage = OpportunityStatus.NEGOTIATION
                opportunity.save()
            
            # Import du serializer devis
            from devis.serializers import QuoteSerializer
            
            return Response({
                'detail': 'Devis créé avec succès depuis l\'opportunité.',
                'quote_id': quote.id,
                'quote': QuoteSerializer(quote).data,
                'opportunity': OpportunitySerializer(opportunity).data
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Statistiques des opportunités avec gestion des valeurs NULL"""
        try:
            queryset = self.get_queryset()
            
            # Queryset pour les calculs (exclut les valeurs NULL)
            queryset_with_amounts = queryset.exclude(estimated_amount__isnull=True)
            
            stats = {
                'total': queryset.count(),
                'by_stage': {},
                'total_estimated_amount': 0,
                'weighted_pipeline': 0,
                'won_this_month': 0,
                'lost_this_month': 0,
                'conversion_rate': 0
            }
            
            # Calculs par statut avec protection NULL
            for stage_choice in OpportunityStatus.choices:
                stage_code, stage_label = stage_choice
                stage_opportunities = queryset.filter(stage=stage_code)
                stage_count = stage_opportunities.count()
                
                # Calcul sécurisé du montant par statut
                stage_opportunities_with_amounts = stage_opportunities.exclude(estimated_amount__isnull=True)
                stage_amounts = stage_opportunities_with_amounts.values_list('estimated_amount', flat=True)
                stage_amount = sum(float(amount) for amount in stage_amounts if amount is not None)
                
                stats['by_stage'][stage_code] = {
                    'label': stage_label,
                    'count': stage_count,
                    'total_amount': float(stage_amount)
                }
            
            # Montant total estimé (protection NULL)
            total_amounts = queryset_with_amounts.values_list('estimated_amount', flat=True)
            stats['total_estimated_amount'] = float(sum(float(amount) for amount in total_amounts if amount is not None))
            
            # Pipeline pondéré (montant * probabilité) avec protection NULL
            weighted_sum = 0
            for opp in queryset_with_amounts:
                if opp.estimated_amount is not None and opp.probability is not None:
                    weighted_sum += float(opp.estimated_amount) * (float(opp.probability) / 100)
            stats['weighted_pipeline'] = float(weighted_sum)
            
            # Opportunités gagnées/perdues ce mois
            current_month = timezone.now().replace(day=1)
            stats['won_this_month'] = queryset.filter(
                stage=OpportunityStatus.WON,
                closed_at__gte=current_month
            ).count()
            
            stats['lost_this_month'] = queryset.filter(
                stage=OpportunityStatus.LOST,
                closed_at__gte=current_month
            ).count()
            
            # Taux de conversion
            total_closed = queryset.filter(stage__in=[OpportunityStatus.WON, OpportunityStatus.LOST]).count()
            won_count = queryset.filter(stage=OpportunityStatus.WON).count()
            if total_closed > 0:
                stats['conversion_rate'] = round((won_count / total_closed) * 100, 2)
            
            return Response(stats)
            
        except Exception as e:
            # Fallback en cas d'erreur
            return Response({
                'total': 0,
                'by_stage': {},
                'total_estimated_amount': 0,
                'weighted_pipeline': 0,
                'won_this_month': 0,
                'lost_this_month': 0,
                'conversion_rate': 0,
                'error': f'Erreur lors du calcul des statistiques: {str(e)}'
            }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'])
    def timeline(self, request, pk=None):
        """Timeline d'une opportunité (pour futures extensions)"""
        opportunity = self.get_object()
        
        timeline = [
            {
                'date': opportunity.created_at,
                'event': 'Création de l\'opportunité',
                'stage': opportunity.stage,
                'details': f"Opportunité créée avec un montant estimé de {opportunity.estimated_amount}€"
            }
        ]
        
        if opportunity.closed_at:
            event = "Opportunité gagnée" if opportunity.stage == OpportunityStatus.WON else "Opportunité perdue"
            timeline.append({
                'date': opportunity.closed_at,
                'event': event,
                'stage': opportunity.stage,
                'details': opportunity.loss_description if opportunity.stage == OpportunityStatus.LOST else f"Projet créé: {opportunity.project_id}"
            })
        
        return Response(timeline)
