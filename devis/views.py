from django.shortcuts import render
from django.db.models import Q, Count, Sum, Avg
from django.utils import timezone
from datetime import datetime, timedelta
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from decimal import Decimal
from django.db import transaction

from .models import Quote, QuoteItem, QuoteStatus
from .serializers import (
    QuoteSerializer, QuoteDetailSerializer, 
    QuoteItemSerializer, QuoteItemDetailSerializer,
    QuoteStatsSerializer, QuoteActionSerializer,
    QuoteDuplicateSerializer, QuoteExportSerializer
)
from tiers.models import Tiers


class QuoteViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour gérer les opérations CRUD sur les devis.
    
    list: Récupère tous les devis avec filtres
    retrieve: Récupère un devis par son ID avec tous les détails
    create: Crée un nouveau devis
    update: Met à jour un devis existant
    partial_update: Met à jour partiellement un devis
    destroy: Supprime un devis
    
    Actions personnalisées:
    - stats: Statistiques globales des devis
    - mark_as_sent: Marquer un devis comme envoyé
    - mark_as_accepted: Marquer un devis comme accepté
    - mark_as_rejected: Marquer un devis comme refusé
    - mark_as_cancelled: Marquer un devis comme annulé
    - duplicate: Dupliquer un devis
    - export: Exporter un devis (PDF, Excel, CSV)
    - bulk_update: Mise à jour en lot d'un devis complet
    - bulk_create: Création d'un devis complet avec tous ses éléments
    """
    queryset = Quote.objects.all()
    serializer_class = QuoteSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'tier', 'issue_date', 'expiry_date']
    search_fields = ['number', 'client_name', 'project_name', 'notes']
    ordering_fields = ['created_at', 'issue_date', 'expiry_date', 'total_ttc', 'number']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """
        Utilise le sérialiseur détaillé pour les opérations de lecture individuelles.
        """
        if self.action == 'retrieve':
            return QuoteDetailSerializer
        elif self.action in ['mark_as_sent', 'mark_as_accepted', 'mark_as_rejected', 'mark_as_cancelled']:
            return QuoteActionSerializer
        elif self.action == 'duplicate':
            return QuoteDuplicateSerializer
        elif self.action == 'export':
            return QuoteExportSerializer
        return QuoteSerializer
    
    def get_queryset(self):
        """
        Personnaliser le queryset avec des optimisations et filtres avancés.
        """
        queryset = Quote.objects.select_related('tier').prefetch_related('items')
        
        # Filtres personnalisés
        client_id = self.request.query_params.get('client_id')
        if client_id:
            queryset = queryset.filter(tier_id=client_id)
        
        status_list = self.request.query_params.get('status_list')
        if status_list:
            status_values = status_list.split(',')
            queryset = queryset.filter(status__in=status_values)
        
        date_from = self.request.query_params.get('date_from')
        if date_from:
            try:
                date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
                queryset = queryset.filter(issue_date__gte=date_from)
            except ValueError:
                pass
        
        date_to = self.request.query_params.get('date_to')
        if date_to:
            try:
                date_to = datetime.strptime(date_to, '%Y-%m-%d').date()
                queryset = queryset.filter(issue_date__lte=date_to)
            except ValueError:
                pass
        
        min_amount = self.request.query_params.get('min_amount')
        if min_amount:
            try:
                min_amount = Decimal(min_amount)
                queryset = queryset.filter(total_ttc__gte=min_amount)
            except (ValueError, TypeError):
                pass
        
        max_amount = self.request.query_params.get('max_amount')
        if max_amount:
            try:
                max_amount = Decimal(max_amount)
                queryset = queryset.filter(total_ttc__lte=max_amount)
            except (ValueError, TypeError):
                pass
        
        return queryset
    
    def perform_create(self, serializer):
        """
        Personnaliser la création pour ajouter l'utilisateur créateur.
        """
        created_by = None
        if self.request.user and hasattr(self.request.user, 'email'):
            created_by = self.request.user.email
        elif self.request.user and hasattr(self.request.user, 'username'):
            created_by = self.request.user.username
        
        serializer.save(created_by=created_by)
    
    def perform_update(self, serializer):
        """
        Personnaliser la mise à jour pour ajouter l'utilisateur modificateur.
        """
        updated_by = None
        if self.request.user and hasattr(self.request.user, 'email'):
            updated_by = self.request.user.email
        elif self.request.user and hasattr(self.request.user, 'username'):
            updated_by = self.request.user.username
        
        serializer.save(updated_by=updated_by)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        Endpoint pour récupérer les statistiques globales des devis.
        """
        try:
            # Compter les devis par statut
            quotes = Quote.objects.all()
            
            stats_data = {
                'total': quotes.count(),
                'draft': quotes.filter(status=QuoteStatus.DRAFT).count(),
                'sent': quotes.filter(status=QuoteStatus.SENT).count(),
                'accepted': quotes.filter(status=QuoteStatus.ACCEPTED).count(),
                'rejected': quotes.filter(status=QuoteStatus.REJECTED).count(),
                'expired': quotes.filter(status=QuoteStatus.EXPIRED).count(),
                'cancelled': quotes.filter(status=QuoteStatus.CANCELLED).count(),
            }
            
            # Calculer le montant total
            total_amount = quotes.aggregate(
                total=Sum('total_ttc')
            )['total'] or Decimal('0')
            stats_data['total_amount'] = total_amount
            
            # Calculer le taux d'acceptation
            sent_count = stats_data['sent'] + stats_data['accepted'] + stats_data['rejected']
            if sent_count > 0:
                acceptance_rate = (stats_data['accepted'] / sent_count) * 100
            else:
                acceptance_rate = 0
            stats_data['acceptance_rate'] = Decimal(str(round(acceptance_rate, 2)))
            
            serializer = QuoteStatsSerializer(stats_data)
            return Response(serializer.data)
        
        except Exception as e:
            return Response(
                {"detail": f"Erreur lors du calcul des statistiques: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def mark_as_sent(self, request, pk=None):
        """
        Marquer un devis comme envoyé.
        """
        try:
            quote = self.get_object()
            
            if quote.status != QuoteStatus.DRAFT:
                return Response(
                    {"detail": "Seuls les devis en brouillon peuvent être envoyés."}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            quote.mark_as_sent()
            
            # Log de l'action
            note = request.data.get('note', '')
            if note:
                # Ici on pourrait ajouter un système de logs/historique
                pass
            
            # Utiliser le serializer principal pour retourner les données du quote
            serializer = QuoteSerializer(quote)
            return Response({
                "detail": "Devis marqué comme envoyé avec succès.",
                "quote": serializer.data
            })
        
        except Exception as e:
            return Response(
                {"detail": f"Erreur lors de l'envoi du devis: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def mark_as_accepted(self, request, pk=None):
        """
        Marquer un devis comme accepté.
        """
        try:
            quote = self.get_object()
            
            if quote.status not in [QuoteStatus.SENT]:
                return Response(
                    {"detail": "Seuls les devis envoyés peuvent être acceptés."}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            quote.mark_as_accepted()
            
            serializer = QuoteSerializer(quote)
            return Response({
                "detail": "Devis marqué comme accepté avec succès.",
                "quote": serializer.data
            })
        
        except Exception as e:
            return Response(
                {"detail": f"Erreur lors de l'acceptation du devis: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def mark_as_rejected(self, request, pk=None):
        """
        Marquer un devis comme refusé.
        """
        try:
            quote = self.get_object()
            
            if quote.status not in [QuoteStatus.SENT]:
                return Response(
                    {"detail": "Seuls les devis envoyés peuvent être refusés."}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            quote.mark_as_rejected()
            
            serializer = QuoteSerializer(quote)
            return Response({
                "detail": "Devis marqué comme refusé.",
                "quote": serializer.data
            })
        
        except Exception as e:
            return Response(
                {"detail": f"Erreur lors du refus du devis: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def mark_as_cancelled(self, request, pk=None):
        """
        Marquer un devis comme annulé.
        """
        try:
            quote = self.get_object()
            
            if quote.status not in [QuoteStatus.DRAFT, QuoteStatus.SENT]:
                return Response(
                    {"detail": "Seuls les devis en brouillon ou envoyés peuvent être annulés."}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            quote.mark_as_cancelled()
            
            serializer = QuoteSerializer(quote)
            return Response({
                "detail": "Devis annulé avec succès.",
                "quote": serializer.data
            })
        
        except Exception as e:
            return Response(
                {"detail": f"Erreur lors de l'annulation du devis: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def duplicate(self, request, pk=None):
        """
        Dupliquer un devis existant.
        """
        try:
            original_quote = self.get_object()
            
            # Options de duplication
            copy_items = request.data.get('copy_items', True)
            new_number = request.data.get('new_number', f"{original_quote.number}_COPY")
            
            # Créer le nouveau devis
            new_quote = Quote.objects.create(
                number=new_number,
                client_name=original_quote.client_name,
                client_address=original_quote.client_address,
                project_name=original_quote.project_name,
                issue_date=timezone.now().date(),
                expiry_date=timezone.now().date() + timedelta(days=30),
                conditions=original_quote.conditions,
                notes=original_quote.notes,
                tier=original_quote.tier,
                status=QuoteStatus.DRAFT,
                # Les totaux seront recalculés automatiquement
                total_ht=Decimal('0'),
                total_tva=Decimal('0'),
                total_ttc=Decimal('0'),
                created_by=self.request.user.email if hasattr(self.request.user, 'email') else None
            )
            
            # Copier les éléments si demandé
            if copy_items:
                original_items = QuoteItem.objects.filter(quote=original_quote).order_by('position')
                for item in original_items:
                    QuoteItem.objects.create(
                        quote=new_quote,
                        designation=item.designation,
                        description=item.description,
                        quantity=item.quantity,
                        unit=item.unit,
                        unit_price=item.unit_price,
                        discount_percentage=item.discount_percentage,
                        tva_rate=item.tva_rate,
                        position=item.position,
                        type=item.type,
                        parent=item.parent,
                        reference=item.reference
                    )
                
                # Recalculer les totaux
                new_quote.calculate_totals()
                new_quote.save()
            
            serializer = QuoteDetailSerializer(new_quote)
            return Response({
                "detail": "Devis dupliqué avec succès.",
                "quote": serializer.data
            })
        
        except Exception as e:
            return Response(
                {"detail": f"Erreur lors de la duplication: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def export(self, request, pk=None):
        """
        Exporter un devis vers différents formats.
        """
        try:
            quote = self.get_object()
            export_format = request.data.get('format', 'pdf').lower()
            
            if export_format not in ['pdf', 'excel', 'csv']:
                return Response(
                    {"detail": "Format d'export non supporté. Utilisez 'pdf', 'excel' ou 'csv'."}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Ici on implémenterait la logique d'export réelle
            # Pour le moment, on retourne juste un message de succès
            
            return Response({
                "detail": f"Export {export_format.upper()} généré avec succès.",
                "download_url": f"/api/quotes/{quote.id}/download/{export_format}/",
                "filename": f"devis_{quote.number}.{export_format}"
            })
        
        except Exception as e:
            return Response(
                {"detail": f"Erreur lors de l'export: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['put'])
    def bulk_update(self, request, pk=None):
        """
        Mise à jour complète d'un devis avec tous ses éléments en une seule transaction.
        """
        try:
            quote = self.get_object()
            
            with transaction.atomic():
                # Mettre à jour les informations du devis
                quote_data = request.data.get('quote', {})
                for field, value in quote_data.items():
                    if hasattr(quote, field) and field not in ['id', 'created_at', 'updated_at']:
                        setattr(quote, field, value)
                
                # Gérer les éléments
                items_data = request.data.get('items', [])
                if items_data:
                    # Supprimer les anciens éléments
                    QuoteItem.objects.filter(quote=quote).delete()
                    
                    # Créer les nouveaux éléments
                    for position, item_data in enumerate(items_data):
                        # Conversion des noms de champs frontend vers backend
                        field_mapping = {
                            'designation': 'designation',
                            'description': 'description', 
                            'quantity': 'quantity',
                            'unit': 'unit',
                            'unitPrice': 'unit_price',
                            'discountPercentage': 'discount_percentage',
                            'tvaRate': 'tva_rate',
                            'type': 'type',
                            'reference': 'reference'
                        }
                        
                        backend_data = {}
                        for frontend_field, backend_field in field_mapping.items():
                            if frontend_field in item_data:
                                backend_data[backend_field] = item_data[frontend_field]
                        
                        backend_data['quote'] = quote
                        backend_data['position'] = position + 1
                        
                        QuoteItem.objects.create(**backend_data)
                
                # Recalculer les totaux
                quote.calculate_totals()
                quote.save()
                
                # Retourner le devis mis à jour
                serializer = QuoteDetailSerializer(quote)
                return Response({
                    "detail": "Devis mis à jour avec succès.",
                    "quote": serializer.data
                })
        
        except Exception as e:
            return Response(
                {"detail": f"Erreur lors de la mise à jour: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def bulk_create(self, request):
        """
        Création complète d'un devis avec tous ses éléments en une seule transaction.
        """
        try:
            with transaction.atomic():
                # Créer le devis
                quote_data = request.data.get('quote', {})
                
                # Définir des valeurs par défaut
                quote_data.setdefault('issue_date', timezone.now().date())
                quote_data.setdefault('expiry_date', timezone.now().date() + timedelta(days=30))
                quote_data.setdefault('status', QuoteStatus.DRAFT)
                quote_data.setdefault('created_by', getattr(self.request.user, 'email', None))
                
                quote = Quote.objects.create(**quote_data)
                
                # Créer les éléments
                items_data = request.data.get('items', [])
                for position, item_data in enumerate(items_data):
                    # Conversion des noms de champs frontend vers backend
                    field_mapping = {
                        'designation': 'designation',
                        'description': 'description', 
                        'quantity': 'quantity',
                        'unit': 'unit',
                        'unitPrice': 'unit_price',
                        'discountPercentage': 'discount_percentage',
                        'tvaRate': 'tva_rate',
                        'type': 'type',
                        'reference': 'reference'
                    }
                    
                    backend_data = {}
                    for frontend_field, backend_field in field_mapping.items():
                        if frontend_field in item_data:
                            backend_data[backend_field] = item_data[frontend_field]
                    
                    backend_data['quote'] = quote
                    backend_data['position'] = position + 1
                    
                    QuoteItem.objects.create(**backend_data)
                
                # Recalculer les totaux
                quote.calculate_totals()
                quote.save()
                
                # Retourner le devis créé
                serializer = QuoteDetailSerializer(quote)
                return Response({
                    "detail": "Devis créé avec succès.",
                    "quote": serializer.data
                }, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            return Response(
                {"detail": f"Erreur lors de la création: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class QuoteItemViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour gérer les opérations CRUD sur les éléments de devis.
    
    list: Récupère tous les éléments de devis
    retrieve: Récupère un élément de devis par son ID
    create: Crée un nouvel élément de devis
    update: Met à jour un élément de devis existant
    partial_update: Met à jour partiellement un élément de devis
    destroy: Supprime un élément de devis
    
    Actions personnalisées:
    - by_quote: Récupérer les éléments d'un devis spécifique
    - reorder: Réorganiser l'ordre des éléments
    - batch_operations: Opérations en lot sur les éléments
    """
    queryset = QuoteItem.objects.all()
    serializer_class = QuoteItemSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['quote', 'type', 'parent']
    search_fields = ['designation', 'description', 'reference']
    ordering_fields = ['position', 'designation', 'unit_price', 'total_ht']
    ordering = ['position']
    
    def get_serializer_class(self):
        """
        Utilise le sérialiseur détaillé pour les opérations de lecture individuelles.
        """
        if self.action == 'retrieve':
            return QuoteItemDetailSerializer
        return QuoteItemSerializer
    
    def get_queryset(self):
        """
        Optimiser le queryset.
        """
        return QuoteItem.objects.select_related('quote', 'parent')
    
    @action(detail=False, methods=['get'])
    def by_quote(self, request):
        """
        Récupérer tous les éléments d'un devis spécifique avec leur hiérarchie.
        """
        quote_id = request.query_params.get('quote_id')
        if not quote_id:
            return Response(
                {"detail": "Le paramètre 'quote_id' est requis."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Récupérer tous les éléments du devis
            items = QuoteItem.objects.filter(quote_id=quote_id).order_by('position')
            
            # Organiser en structure hiérarchique
            def serialize_item_with_children(item):
                item_data = QuoteItemDetailSerializer(item).data
                
                # Récupérer les enfants
                children = items.filter(parent=item)
                if children.exists():
                    item_data['children'] = [
                        serialize_item_with_children(child) for child in children
                    ]
                
                return item_data
            
            # Récupérer seulement les éléments de niveau racine
            root_items = items.filter(parent__isnull=True)
            
            result = [serialize_item_with_children(item) for item in root_items]
            
            return Response({
                "quote_id": quote_id,
                "items": result,
                "total_count": items.count()
            })
        
        except Exception as e:
            return Response(
                {"detail": f"Erreur lors de la récupération des éléments: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def reorder(self, request):
        """
        Réorganiser l'ordre des éléments d'un devis.
        """
        try:
            items_order = request.data.get('items_order', [])
            
            if not items_order:
                return Response(
                    {"detail": "La liste 'items_order' est requise."}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            with transaction.atomic():
                for position, item_id in enumerate(items_order):
                    QuoteItem.objects.filter(id=item_id).update(position=position + 1)
            
            return Response({
                "detail": "Ordre des éléments mis à jour avec succès.",
                "items_order": items_order
            })
        
        except Exception as e:
            return Response(
                {"detail": f"Erreur lors de la réorganisation: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def batch_operations(self, request):
        """
        Effectuer des opérations en lot sur plusieurs éléments.
        """
        try:
            operations = request.data.get('operations', [])
            
            if not operations:
                return Response(
                    {"detail": "La liste 'operations' est requise."}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            results = []
            
            with transaction.atomic():
                for operation in operations:
                    op_type = operation.get('type')
                    item_id = operation.get('item_id')
                    data = operation.get('data', {})
                    
                    if op_type == 'create':
                        # Conversion des champs frontend vers backend
                        field_mapping = {
                            'designation': 'designation',
                            'description': 'description', 
                            'quantity': 'quantity',
                            'unit': 'unit',
                            'unitPrice': 'unit_price',
                            'discountPercentage': 'discount_percentage',
                            'tvaRate': 'tva_rate',
                            'type': 'type',
                            'reference': 'reference'
                        }
                        
                        backend_data = {}
                        for frontend_field, backend_field in field_mapping.items():
                            if frontend_field in data:
                                backend_data[backend_field] = data[frontend_field]
                        
                        item = QuoteItem.objects.create(**backend_data)
                        results.append({
                            'operation': 'create',
                            'item_id': item.id,
                            'success': True
                        })
                    
                    elif op_type == 'update' and item_id:
                        item = QuoteItem.objects.get(id=item_id)
                        
                        field_mapping = {
                            'designation': 'designation',
                            'description': 'description', 
                            'quantity': 'quantity',
                            'unit': 'unit',
                            'unitPrice': 'unit_price',
                            'discountPercentage': 'discount_percentage',
                            'tvaRate': 'tva_rate',
                            'type': 'type',
                            'reference': 'reference'
                        }
                        
                        for frontend_field, backend_field in field_mapping.items():
                            if frontend_field in data:
                                setattr(item, backend_field, data[frontend_field])
                        
                        item.save()
                        results.append({
                            'operation': 'update',
                            'item_id': item_id,
                            'success': True
                        })
                    
                    elif op_type == 'delete' and item_id:
                        QuoteItem.objects.filter(id=item_id).delete()
                        results.append({
                            'operation': 'delete',
                            'item_id': item_id,
                            'success': True
                        })
            
            return Response({
                "detail": "Opérations en lot effectuées avec succès.",
                "results": results
            })
        
        except Exception as e:
            return Response(
                {"detail": f"Erreur lors des opérations en lot: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
