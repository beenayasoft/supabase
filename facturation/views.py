from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q, Sum, Count, Avg
from django.db.models.functions import Coalesce
from django.http import HttpResponse
from datetime import datetime, timedelta
import uuid

from .models import Invoice, InvoiceItem, Payment, InvoiceStatus
from .serializers import (
    InvoiceDetailSerializer, InvoiceListSerializer, InvoiceCreateSerializer,
    InvoiceItemSerializer, PaymentSerializer, InvoiceFromQuoteSerializer,
    ValidateInvoiceSerializer, RecordPaymentSerializer, CreateCreditNoteSerializer,
    InvoiceStatsSerializer, InvoiceFilterSerializer
)
from .pdf_generator import InvoicePDFGenerator
from devis.models import Quote  # Import pour créer depuis devis
from tiers.models import Tiers


class InvoiceViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour les factures - Implémente toutes les user stories
    """
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Queryset avec optimisations et filtres"""
        queryset = Invoice.objects.select_related('tier').prefetch_related(
            'items', 'payments'
        ).all()
        
        # Appliquer les filtres
        filter_serializer = InvoiceFilterSerializer(data=self.request.query_params)
        if filter_serializer.is_valid():
            filters = filter_serializer.validated_data
            
            # Filtres par statut
            if filters.get('status'):
                queryset = queryset.filter(status__in=filters['status'])
            
            # Filtres par client
            if filters.get('client_id'):
                queryset = queryset.filter(tier_id=filters['client_id'])
            
            # Filtres par projet
            if filters.get('project_id'):
                queryset = queryset.filter(project_reference=filters['project_id'])
            
            # Filtres par date
            if filters.get('date_from'):
                queryset = queryset.filter(issue_date__gte=filters['date_from'])
            if filters.get('date_to'):
                queryset = queryset.filter(issue_date__lte=filters['date_to'])
            
            # Filtres par montant
            if filters.get('amount_min'):
                queryset = queryset.filter(total_ttc__gte=filters['amount_min'])
            if filters.get('amount_max'):
                queryset = queryset.filter(total_ttc__lte=filters['amount_max'])
            
            # Recherche textuelle
            if filters.get('search'):
                search_term = filters['search']
                queryset = queryset.filter(
                    Q(number__icontains=search_term) |
                    Q(client_name__icontains=search_term) |
                    Q(project_name__icontains=search_term) |
                    Q(notes__icontains=search_term)
                )
        
        return queryset.order_by('-created_at')
    
    def get_serializer_class(self):
        """Choisir le serializer selon l'action"""
        if self.action == 'list':
            return InvoiceListSerializer
        elif self.action == 'create':
            return InvoiceCreateSerializer
        else:
            return InvoiceDetailSerializer
    
    def perform_create(self, serializer):
        """Personnaliser la création avec l'utilisateur actuel"""
        serializer.save(created_by=self.request.user.email if self.request.user else None)
    
    def perform_update(self, serializer):
        """Personnaliser la mise à jour avec l'utilisateur actuel"""
        serializer.save(updated_by=self.request.user.email if self.request.user else None)
    
    @action(detail=False, methods=['post'], url_path='from-quote')
    def create_from_quote(self, request):
        """
        US 5.1: Créer une facture depuis un devis
        POST /api/invoices/from-quote/
        """
        serializer = InvoiceFromQuoteSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            
            try:
                # Récupérer le devis
                quote = get_object_or_404(Quote, id=data['quote_id'])
                
                # Créer la facture de base avec les données du devis
                invoice_data = {
                    'tier': quote.tier,
                    'quote': quote,  # La relation directe permettra de récupérer toutes les infos automatiquement
                    'payment_terms': data.get('payment_terms', 30),
                    'notes': data.get('notes', ''),
                    'terms_and_conditions': data.get('terms_and_conditions', quote.terms_and_conditions),
                    'created_by': request.user.email if request.user else None
                }
                
                # Permettre de surcharger les informations si fournies explicitement
                if data.get('client_name'):
                    invoice_data['client_name'] = data['client_name']
                if data.get('client_address'):
                    invoice_data['client_address'] = data['client_address']
                if data.get('project_name'):
                    invoice_data['project_name'] = data['project_name']
                if data.get('project_address'):
                    invoice_data['project_address'] = data['project_address']
                if data.get('project_reference'):
                    invoice_data['project_reference'] = data['project_reference']
                
                invoice = Invoice.objects.create(**invoice_data)
                
                # Copier les éléments selon le type de facture
                if data['invoice_type'] == 'total':
                    # Facture totale - copier tous les éléments
                    for quote_item in quote.items.all():
                        InvoiceItem.objects.create(
                            invoice=invoice,
                            type=quote_item.type,
                            parent=quote_item.parent,
                            position=quote_item.position,
                            reference=quote_item.reference,
                            designation=quote_item.designation,
                            description=quote_item.description,
                            unit=quote_item.unit,
                            quantity=quote_item.quantity,
                            unit_price=quote_item.unit_price,
                            discount=quote_item.discount,
                            vat_rate=quote_item.vat_rate,
                            work_id=quote_item.work_id
                        )
                
                elif data['invoice_type'] == 'acompte':
                    # Facture d'acompte - créer un élément unique
                    acompte_percentage = data['acompte_percentage']
                    acompte_amount = quote.total_ht * (acompte_percentage / 100)
                    
                    InvoiceItem.objects.create(
                        invoice=invoice,
                        type='advance_payment',
                        designation=f'Acompte {acompte_percentage}% - Devis N°{quote.number}',
                        quantity=1,
                        unit_price=acompte_amount,
                        vat_rate='20'  # TVA standard par défaut
                    )
                
                # Mettre à jour les totaux
                invoice.update_totals()
                
                # Retourner la facture créée
                response_serializer = InvoiceDetailSerializer(invoice)
                return Response(response_serializer.data, status=status.HTTP_201_CREATED)
                
            except Quote.DoesNotExist:
                return Response(
                    {'error': 'Devis non trouvé'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            except Exception as e:
                return Response(
                    {'error': f'Erreur lors de la création: {str(e)}'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'], url_path='validate')
    def validate_invoice(self, request, pk=None):
        """
        US 5.3: Valider et émettre une facture
        POST /api/invoices/{id}/validate/
        """
        invoice = self.get_object()
        
        try:
            invoice.validate_and_send()
            serializer = InvoiceDetailSerializer(invoice)
            return Response(serializer.data)
        
        except ValueError as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': f'Erreur lors de la validation: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'], url_path='record-payment')
    def record_payment(self, request, pk=None):
        """
        US 5.4: Enregistrer un règlement
        POST /api/invoices/{id}/record-payment/
        """
        invoice = self.get_object()
        serializer = RecordPaymentSerializer(data=request.data)
        
        if serializer.is_valid():
            data = serializer.validated_data
            
            try:
                payment = invoice.record_payment(
                    amount=data['amount'],
                    method=data['method'],
                    date=data.get('date'),
                    reference=data.get('reference'),
                    notes=data.get('notes')
                )
                
                payment_serializer = PaymentSerializer(payment)
                return Response({
                    'payment': payment_serializer.data,
                    'invoice': InvoiceDetailSerializer(invoice).data
                })
            
            except ValueError as e:
                return Response(
                    {'error': str(e)}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            except Exception as e:
                return Response(
                    {'error': f'Erreur lors de l\'enregistrement: {str(e)}'}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'], url_path='create-credit-note')
    def create_credit_note(self, request, pk=None):
        """
        US 5.5: Créer un avoir
        POST /api/invoices/{id}/create-credit-note/
        """
        invoice = self.get_object()
        serializer = CreateCreditNoteSerializer(data=request.data)
        
        if serializer.is_valid():
            data = serializer.validated_data
            
            try:
                credit_note = invoice.create_credit_note(
                    reason=data.get('reason', ''),
                    is_full_credit_note=data.get('is_full_credit_note', True),
                    selected_items=data.get('selected_items')
                )
                
                response_serializer = InvoiceDetailSerializer(credit_note)
                return Response(response_serializer.data, status=status.HTTP_201_CREATED)
            
            except ValueError as e:
                return Response(
                    {'error': str(e)}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            except Exception as e:
                return Response(
                    {'error': f'Erreur lors de la création de l\'avoir: {str(e)}'}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'], url_path='stats')
    def get_stats(self, request):
        """
        Obtenir les statistiques de facturation
        GET /api/invoices/stats/
        """
        # Compter les factures par statut
        stats = Invoice.objects.aggregate(
            total_invoices=Count('id'),
            draft_invoices=Count('id', filter=Q(status=InvoiceStatus.DRAFT)),
            sent_invoices=Count('id', filter=Q(status=InvoiceStatus.SENT)),
            paid_invoices=Count('id', filter=Q(status=InvoiceStatus.PAID)),
            overdue_invoices=Count('id', filter=Q(status=InvoiceStatus.OVERDUE)),
            partially_paid_invoices=Count('id', filter=Q(status=InvoiceStatus.PARTIALLY_PAID)),
            cancelled_invoices=Count('id', filter=Q(status=InvoiceStatus.CANCELLED)),
            credit_note_invoices=Count('id', filter=Q(status=InvoiceStatus.CANCELLED_BY_CREDIT_NOTE)),
            total_amount_ht=Coalesce(Sum('total_ht'), 0),
            total_amount_ttc=Coalesce(Sum('total_ttc'), 0),
            total_paid=Coalesce(Sum('paid_amount'), 0),
        )
        
        # Calculer le restant dû
        stats['total_outstanding'] = stats['total_amount_ttc'] - stats['total_paid']
        
        # Calculer le montant des factures en retard
        overdue_invoices = Invoice.objects.filter(status=InvoiceStatus.OVERDUE)
        stats['overdue_amount'] = overdue_invoices.aggregate(
            total=Coalesce(Sum('remaining_amount'), 0)
        )['total']
        
        # Calculer le délai moyen de paiement
        paid_invoices = Invoice.objects.filter(
            status=InvoiceStatus.PAID,
            payments__isnull=False
        ).distinct()
        
        if paid_invoices.exists():
            total_days = 0
            count = 0
            
            for invoice in paid_invoices:
                # Trouver le dernier paiement
                last_payment = invoice.payments.order_by('-date').first()
                if last_payment and invoice.issue_date:
                    # Calculer le délai en jours
                    payment_delay = (last_payment.date - invoice.issue_date).days
                    total_days += payment_delay
                    count += 1
            
            stats['average_payment_delay'] = total_days / count if count > 0 else 0
        else:
            stats['average_payment_delay'] = 0
        
        serializer = InvoiceStatsSerializer(stats)
        return Response(serializer.data)

    @action(detail=True, methods=['get'], url_path='deletion-constraints')
    def get_deletion_constraints(self, request, pk=None):
        """
        Vérifier les contraintes de suppression d'une facture
        GET /api/invoices/{id}/deletion-constraints/
        """
        try:
            invoice = self.get_object()
            constraints = []
            can_delete = True
            
            # Vérifier le statut - seuls les brouillons peuvent être supprimés
            if invoice.status != InvoiceStatus.DRAFT:
                constraints.append({
                    'type': 'status',
                    'message': f'Impossible de supprimer une facture avec le statut "{invoice.get_status_display()}"',
                    'blocking': True
                })
                can_delete = False
            
            # Vérifier les paiements
            if invoice.payments.exists():
                payment_count = invoice.payments.count()
                total_paid = invoice.paid_amount
                constraints.append({
                    'type': 'payments',
                    'message': f'Cette facture a {payment_count} paiement(s) enregistré(s) pour un total de {total_paid} MAD',
                    'blocking': True
                })
                can_delete = False
            
            # Vérifier les avoirs liés (en utilisant une méthode sécurisée)
            try:
                if hasattr(invoice, 'credit_notes'):
                    credit_notes = invoice.credit_notes.all()
                    if credit_notes.exists():
                        constraints.append({
                            'type': 'credit_notes',
                            'message': f'Cette facture a {credit_notes.count()} avoir(s) associé(s)',
                            'blocking': True
                        })
                        can_delete = False
            except Exception as e:
                # En cas d'erreur avec les avoirs, on ajoute une contrainte non bloquante
                constraints.append({
                    'type': 'credit_notes',
                    'message': 'Impossible de vérifier les avoirs liés',
                    'blocking': False
                })
                print(f"Erreur lors de la vérification des avoirs: {str(e)}")
            
            # Avertissements non bloquants
            if invoice.status == InvoiceStatus.DRAFT and invoice.items.count() > 0:
                constraints.append({
                    'type': 'items',
                    'message': f'Cette facture contient {invoice.items.count()} élément(s)',
                    'blocking': False
                })
            
            return Response({
                'canDelete': can_delete,
                'constraints': constraints
            })
        except Exception as e:
            print(f"Erreur lors de la vérification des contraintes: {str(e)}")
            return Response({
                'canDelete': False,
                'constraints': [{
                    'type': 'error',
                    'message': f'Erreur lors de la vérification des contraintes: {str(e)}',
                    'blocking': True
                }]
            }, status=status.HTTP_200_OK)  # On retourne 200 avec un message d'erreur au lieu de 500

    @action(detail=True, methods=['get'], url_path='payment-impact')
    def get_payment_impact(self, request, pk=None):
        """
        Simuler l'impact d'un paiement sur une facture
        GET /api/invoices/{id}/payment-impact/?amount=1000
        """
        invoice = self.get_object()
        
        try:
            amount = float(request.query_params.get('amount', 0))
            if amount <= 0:
                return Response(
                    {'error': 'Le montant doit être supérieur à 0'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Calculer le nouveau reste à payer
            new_remaining = invoice.remaining_amount - amount
            
            # Déterminer le nouveau statut
            if new_remaining <= 0:
                new_status = InvoiceStatus.PAID
            elif invoice.paid_amount + amount > 0:
                new_status = InvoiceStatus.PARTIALLY_PAID
            else:
                new_status = invoice.status
            
            return Response({
                'newStatus': new_status,
                'newRemainingAmount': max(0, new_remaining)
            })
            
        except (ValueError, TypeError):
            return Response(
                {'error': 'Montant invalide'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'], url_path='credit-note-preview')
    def get_credit_note_preview(self, request, pk=None):
        """
        Obtenir un aperçu de l'avoir avant création
        POST /api/invoices/{id}/credit-note-preview/
        """
        invoice = self.get_object()
        
        is_full = request.data.get('is_full', True)
        selected_items = request.data.get('selected_items', [])
        
        try:
            total_ht = 0
            total_vat = 0
            total_ttc = 0
            
            if is_full:
                # Avoir total - reprendre tous les montants
                total_ht = invoice.total_ht
                total_vat = invoice.total_vat
                total_ttc = invoice.total_ttc
            else:
                # Avoir partiel - calculer selon les éléments sélectionnés
                if not selected_items:
                    return Response(
                        {'error': 'Aucun élément sélectionné pour l\'avoir partiel'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                items = invoice.items.filter(id__in=selected_items)
                for item in items:
                    item_ht = item.quantity * item.unit_price * (1 - item.discount / 100)
                    item_vat = item_ht * (item.vat_rate / 100)
                    total_ht += item_ht
                    total_vat += item_vat
                    total_ttc += item_ht + item_vat
            
            # Déterminer l'impact
            if total_ttc >= invoice.total_ttc:
                impact = "La facture sera totalement annulée par cet avoir"
            else:
                impact = f"Un avoir de {total_ttc} MAD sera créé, réduisant le montant de la facture"
            
            return Response({
                'totalHT': total_ht,
                'totalVAT': total_vat,
                'totalTTC': total_ttc,
                'impact': impact
            })
            
        except Exception as e:
            return Response(
                {'error': f'Erreur lors du calcul de l\'aperçu: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'], url_path='export')
    def export_invoice(self, request, pk=None):
        """
        Exporter une facture au format PDF
        POST /api/invoices/{id}/export/
        """
        invoice = self.get_object()
        
        try:
            # Générer le PDF
            pdf_generator = InvoicePDFGenerator(invoice)
            pdf_content = pdf_generator.generate_pdf()
            
            # Créer la réponse HTTP avec le contenu PDF
            response = HttpResponse(pdf_content, content_type='application/pdf')
            
            # Définir le nom du fichier pour le téléchargement
            filename = f"Facture_{invoice.number.replace('/', '_')}.pdf"
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            
            return response
            
        except Exception as e:
            return Response(
                {'error': f'Erreur lors de la génération du PDF: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class InvoiceItemViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour les éléments de facture
    """
    serializer_class = InvoiceItemSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filtrer par facture si spécifié"""
        queryset = InvoiceItem.objects.select_related('invoice').all()
        
        invoice_id = self.request.query_params.get('invoice_id')
        if invoice_id:
            queryset = queryset.filter(invoice_id=invoice_id)
        
        return queryset.order_by('position')
    
    def perform_create(self, serializer):
        """Mettre à jour les totaux après création"""
        item = serializer.save()
        if item.invoice:
            item.invoice.update_totals()
    
    def perform_update(self, serializer):
        """Mettre à jour les totaux après modification"""
        item = serializer.save()
        if item.invoice:
            item.invoice.update_totals()
    
    def perform_destroy(self, instance):
        """Mettre à jour les totaux après suppression"""
        invoice = instance.invoice
        instance.delete()
        if invoice:
            invoice.update_totals()


class PaymentViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour les paiements
    """
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filtrer par facture si spécifié"""
        queryset = Payment.objects.select_related('invoice').all()
        
        invoice_id = self.request.query_params.get('invoice_id')
        if invoice_id:
            queryset = queryset.filter(invoice_id=invoice_id)
        
        return queryset.order_by('-date', '-created_at')
    
    def perform_create(self, serializer):
        """Mettre à jour les montants de la facture après création du paiement"""
        payment = serializer.save()
        
        # Mettre à jour les montants de la facture
        invoice = payment.invoice
        invoice.paid_amount = invoice.payments.aggregate(
            total=Coalesce(Sum('amount'), 0)
        )['total']
        invoice.remaining_amount = invoice.total_ttc - invoice.paid_amount
        
        # Mettre à jour le statut si nécessaire
        if invoice.remaining_amount <= 0:
            invoice.status = InvoiceStatus.PAID
        elif invoice.paid_amount > 0 and invoice.remaining_amount > 0:
            invoice.status = InvoiceStatus.PARTIALLY_PAID
        
        invoice.save()
    
    def perform_destroy(self, instance):
        """Mettre à jour les montants après suppression du paiement"""
        invoice = instance.invoice
        instance.delete()
        
        # Recalculer les montants
        invoice.paid_amount = invoice.payments.aggregate(
            total=Coalesce(Sum('amount'), 0)
        )['total']
        invoice.remaining_amount = invoice.total_ttc - invoice.paid_amount
        
        # Mettre à jour le statut
        if invoice.paid_amount == 0:
            invoice.status = InvoiceStatus.SENT
        elif invoice.remaining_amount > 0:
            invoice.status = InvoiceStatus.PARTIALLY_PAID
        
        invoice.save()
