from django.shortcuts import render
from django.db.models import Q, Count, Sum, Avg
from django.utils import timezone
from datetime import datetime, timedelta
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
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


class QuotesPagination(PageNumberPagination):
    """Pagination optimisée pour les devis"""
    page_size = 10  # 10 devis par page par défaut
    page_size_query_param = 'page_size'
    max_page_size = 50  # Maximum 50 devis par page
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
    pagination_class = QuotesPagination  # 📊 OPTIMISATION: Pagination côté backend
    
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
        🚀 OPTIMISÉ : Préchargement des relations pour éviter N+1
        """
        queryset = Quote.objects.select_related('tier').prefetch_related(
            'items',  # Précharger les éléments du devis
        )
        
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
    
    @action(detail=False, methods=['get'], permission_classes=[])
    def stats(self, request):
        """
        Endpoint dédié pour les statistiques globales des devis - OPTIMISÉ
        🚀 Calcule sur TOUS les devis (pas seulement la page courante)
        """
        try:
            # Récupérer TOUS les devis (sans pagination) pour calculer les vraies stats
            all_queryset = self.get_queryset()
            
            # Appliquer seulement le filtre de recherche si présent (pas la pagination)
            search = request.query_params.get('search', '')
            if search:
                all_queryset = all_queryset.filter(
                    Q(number__icontains=search) |
                    Q(client_name__icontains=search) |
                    Q(project_name__icontains=search) |
                    Q(notes__icontains=search)
                ).distinct()
            
            total_count = all_queryset.count()
            
            # Compter par statut de manière optimisée
            draft_count = all_queryset.filter(status='draft').count()
            sent_count = all_queryset.filter(status='sent').count()
            accepted_count = all_queryset.filter(status='accepted').count()
            rejected_count = all_queryset.filter(status='rejected').count()
            expired_count = all_queryset.filter(status='expired').count()
            cancelled_count = all_queryset.filter(status='cancelled').count()
            
            # Calculer le montant total de manière optimisée
            total_amount_aggregate = all_queryset.aggregate(
                total=Sum('total_ttc')
            )['total'] or 0
            total_amount = float(total_amount_aggregate)
            
            # Calculer le taux d'acceptation
            total_decisions = sent_count + accepted_count + rejected_count
            acceptance_rate = 0
            if total_decisions > 0:
                acceptance_rate = round((accepted_count / total_decisions) * 100, 2)
            
            # Données de réponse
            stats_data = {
                'total': total_count,
                'draft': draft_count,
                'sent': sent_count,
                'accepted': accepted_count,
                'rejected': rejected_count,
                'expired': expired_count,
                'cancelled': cancelled_count,
                'total_amount': total_amount,
                'acceptance_rate': acceptance_rate
            }
            
            return Response(stats_data)
        
        except Exception as e:
            # Réponse de fallback en cas d'erreur
            fallback_stats = {
                'total': 0,
                'draft': 0,
                'sent': 0,
                'accepted': 0,
                'rejected': 0,
                'expired': 0,
                'cancelled': 0,
                'total_amount': 0,
                'acceptance_rate': 0,
                'error': f"Erreur : {str(e)}"
            }
            return Response(fallback_stats)
    
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
                terms_and_conditions=original_quote.terms_and_conditions,
                notes=original_quote.notes,
                tier=original_quote.tier,
                status=QuoteStatus.DRAFT,
                # Les totaux seront recalculés automatiquement
                total_ht=Decimal('0'),
                total_vat=Decimal('0'),
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
                        discount=item.discount,
                        vat_rate=item.vat_rate,
                        position=item.position,
                        type=item.type,
                        parent=item.parent,
                        reference=item.reference
                    )
                
                # Recalculer les totaux
                new_quote.update_totals()
            
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
                
                # ✅ CONVERSION FRONTEND → BACKEND - Mapper les champs correctement
                field_mapping = {
                    'tier': 'tier_id',  # UUID string → tier_id pour Django ORM
                    'conditions': 'terms_and_conditions',  # Frontend 'conditions' → Backend 'terms_and_conditions'
                    'issueDate': 'issue_date',  # CamelCase → snake_case
                    'expiryDate': 'expiry_date',  # CamelCase → snake_case
                }
                
                # Appliquer les mappings et mettre à jour le devis
                for frontend_field, value in quote_data.items():
                    backend_field = field_mapping.get(frontend_field, frontend_field)
                    if hasattr(quote, backend_field) and backend_field not in ['id', 'created_at', 'updated_at']:
                        # ✅ VALIDATION TIER - Vérifier que le client existe si on met à jour le tier
                        if backend_field == 'tier_id' and value:
                            if not Tiers.objects.filter(id=value).exists():
                                return Response(
                                    {"detail": f"Le client avec l'ID {value} n'existe pas."}, 
                                    status=status.HTTP_400_BAD_REQUEST
                                )
                        setattr(quote, backend_field, value)
                
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
                            'discount': 'discount',
                            'vat_rate': 'vat_rate',
                            'type': 'type',
                            'reference': 'reference'
                        }
                        
                        backend_data = {}
                        for frontend_field, backend_field in field_mapping.items():
                            if frontend_field in item_data:
                                value = item_data[frontend_field]
                                
                                # ✅ CONVERSION EN DECIMAL pour éviter les conflits de types
                                if backend_field in ['quantity', 'unit_price', 'discount', 'margin']:
                                    try:
                                        from decimal import Decimal
                                        # Convertir en Decimal pour compatibilité avec Django DecimalField
                                        backend_data[backend_field] = Decimal(str(value))
                                        print(f"🔄 UPDATE - Converted {backend_field}: {value} ({type(value).__name__}) → {backend_data[backend_field]} (Decimal)")
                                    except (ValueError, TypeError) as e:
                                        print(f"⚠️ Erreur conversion Decimal {backend_field}: {value} -> {e}")
                                        backend_data[backend_field] = value  # Fallback à la valeur originale
                                else:
                                    # ✅ AUTRES CHAMPS - pas de conversion
                                    backend_data[backend_field] = value
                        
                        # ✅ GÉRER margin s'il existe dans item_data mais pas dans field_mapping
                        if 'margin' in item_data:
                            try:
                                from decimal import Decimal
                                backend_data['margin'] = Decimal(str(item_data['margin']))
                                print(f"🔄 UPDATE - Converted margin: {item_data['margin']} → {backend_data['margin']} (Decimal)")
                            except (ValueError, TypeError) as e:
                                print(f"⚠️ Erreur conversion Decimal margin: {item_data['margin']} -> {e}")
                                backend_data['margin'] = item_data['margin']
                        
                        backend_data['quote'] = quote
                        backend_data['position'] = position + 1
                        
                        QuoteItem.objects.create(**backend_data)
                
                # Recalculer les totaux
                quote.update_totals()
                
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
                
                # ✅ CONVERSION FRONTEND → BACKEND - Mapper les champs correctement
                field_mapping = {
                    'tier': 'tier_id',  # UUID string → tier_id pour Django ORM
                    'conditions': 'terms_and_conditions',  # Frontend 'conditions' → Backend 'terms_and_conditions'
                    'issueDate': 'issue_date',  # CamelCase → snake_case
                    # SUPPRIMER : 'expiryDate': 'expiry_date',  # ❌ NE PAS MAPPER - calculé automatiquement
                }
                
                # Appliquer les mappings de champs avec gestion spéciale des dates
                backend_quote_data = {}
                for frontend_field, value in quote_data.items():
                    backend_field = field_mapping.get(frontend_field, frontend_field)
                    
                    # ✅ IGNORER COMPLÈTEMENT expiryDate - sera calculé automatiquement par le modèle
                    if frontend_field == 'expiryDate':
                        print(f"🚫 Ignoring expiryDate from frontend: {value} (will be calculated automatically)")
                        continue
                    
                    # ✅ GESTION SPÉCIALE DE issue_date
                    if backend_field == 'issue_date':
                        if value and value.strip():
                            try:
                                from datetime import datetime
                                parsed_date = datetime.strptime(value, '%Y-%m-%d').date()
                                backend_quote_data[backend_field] = parsed_date
                                print(f"✅ Parsed issue_date: {value} -> {parsed_date}")
                            except (ValueError, TypeError) as e:
                                print(f"⚠️ Erreur parsing date {backend_field}: {value} -> {e}")
                                # Utiliser la date par défaut
                        continue
                    
                    # ✅ GESTION STANDARD DES AUTRES CHAMPS
                    backend_quote_data[backend_field] = value
                
                # Définir des valeurs par défaut
                backend_quote_data.setdefault('issue_date', timezone.now().date())
                # SUPPRIMER : backend_quote_data.setdefault('expiry_date', timezone.now().date() + timedelta(days=30))
                backend_quote_data.setdefault('status', QuoteStatus.DRAFT)
                backend_quote_data.setdefault('created_by', getattr(self.request.user, 'email', None))
                
                # ✅ VALIDATION TIER - Vérifier que le client existe
                if 'tier_id' in backend_quote_data:
                    tier_id = backend_quote_data['tier_id']
                    if not Tiers.objects.filter(id=tier_id).exists():
                        return Response(
                            {"detail": f"Le client avec l'ID {tier_id} n'existe pas."}, 
                            status=status.HTTP_400_BAD_REQUEST
                        )
                
                quote = Quote.objects.create(**backend_quote_data)
                
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
                        'discount': 'discount',
                        'vat_rate': 'vat_rate',
                        'type': 'type',
                        'reference': 'reference'
                    }
                    
                    backend_data = {}
                    for frontend_field, backend_field in field_mapping.items():
                        if frontend_field in item_data:
                            value = item_data[frontend_field]
                            
                            # ✅ CONVERSION EN DECIMAL pour éviter les conflits de types
                            if backend_field in ['quantity', 'unit_price', 'discount', 'margin']:
                                try:
                                    from decimal import Decimal
                                    # Convertir en Decimal pour compatibilité avec Django DecimalField
                                    backend_data[backend_field] = Decimal(str(value))
                                    print(f"🔢 Converted {backend_field}: {value} ({type(value).__name__}) → {backend_data[backend_field]} (Decimal)")
                                except (ValueError, TypeError) as e:
                                    print(f"⚠️ Erreur conversion Decimal {backend_field}: {value} -> {e}")
                                    backend_data[backend_field] = value  # Fallback à la valeur originale
                            else:
                                # ✅ AUTRES CHAMPS - pas de conversion
                                backend_data[backend_field] = value
                    
                    # ✅ GÉRER margin s'il existe dans item_data mais pas dans field_mapping
                    if 'margin' in item_data:
                        try:
                            from decimal import Decimal
                            backend_data['margin'] = Decimal(str(item_data['margin']))
                            print(f"🔢 Converted margin: {item_data['margin']} → {backend_data['margin']} (Decimal)")
                        except (ValueError, TypeError) as e:
                            print(f"⚠️ Erreur conversion Decimal margin: {item_data['margin']} -> {e}")
                            backend_data['margin'] = item_data['margin']
                    
                    backend_data['quote'] = quote
                    backend_data['position'] = position + 1
                    
                    QuoteItem.objects.create(**backend_data)
                
                # Recalculer les totaux
                quote.update_totals()
                
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
                            'discount': 'discount',
                            'vat_rate': 'vat_rate',
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
                            'discount': 'discount',
                            'vat_rate': 'vat_rate',
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
