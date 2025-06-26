from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db import models
from .models import Invoice, InvoiceItem, Payment


class InvoiceItemInline(admin.TabularInline):
    """Inline pour les éléments de facture"""
    model = InvoiceItem
    extra = 0
    fields = [
        'position', 'type', 'parent', 'reference', 'designation', 'description',
        'quantity', 'unit', 'unit_price', 'discount', 'vat_rate',
        'total_ht', 'total_ttc'
    ]
    readonly_fields = ['total_ht', 'total_ttc']
    ordering = ['position']


class PaymentInline(admin.TabularInline):
    """Inline pour les paiements"""
    model = Payment
    extra = 0
    fields = ['date', 'amount', 'method', 'reference', 'notes']
    readonly_fields = ['created_at']


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    """Administration des factures"""
    
    list_display = [
        'number', 'client_name', 'status_colored', 'issue_date', 'due_date',
        'total_ttc', 'paid_amount', 'remaining_amount', 'created_at'
    ]
    
    list_filter = [
        'status', 'issue_date', 'due_date', 'created_at'
    ]
    
    search_fields = [
        'number', 'client_name', 'project_name', 'notes'
    ]
    
    readonly_fields = [
        'id', 'client_id', 'project_id', 'quote_id', 'credit_note_id', 'original_invoice_id',
        'total_ht', 'total_vat', 'total_ttc', 'remaining_amount', 'created_at', 'updated_at'
    ]
    
    fieldsets = (
        ('Informations générales', {
            'fields': (
                'id', 'number', 'status', 'tier'
            )
        }),
        ('Client et projet', {
            'fields': (
                'client_id', 'client_name', 'client_address',
                'project_name', 'project_address', 'project_reference'
            )
        }),
        ('Dates et conditions', {
            'fields': (
                'issue_date', 'due_date', 'payment_terms'
            )
        }),
        ('Contenu', {
            'fields': (
                'notes', 'terms_and_conditions'
            )
        }),
        ('Montants', {
            'fields': (
                'total_ht', 'total_vat', 'total_ttc',
                'paid_amount', 'remaining_amount'
            ),
            'classes': ('collapse',)
        }),
        ('Liens avec autres documents', {
            'fields': (
                'quote', 'quote_number', 'credit_note', 'original_invoice'
            ),
            'classes': ('collapse',)
        }),
        ('Métadonnées', {
            'fields': (
                'created_at', 'updated_at', 'created_by', 'updated_by'
            ),
            'classes': ('collapse',)
        })
    )
    
    inlines = [InvoiceItemInline, PaymentInline]
    
    actions = ['validate_invoices', 'mark_as_paid']
    
    def status_colored(self, obj):
        """Afficher le statut avec une couleur"""
        colors = {
            'draft': '#6c757d',      # Gris
            'sent': '#007bff',       # Bleu
            'overdue': '#dc3545',    # Rouge
            'partially_paid': '#fd7e14',  # Orange
            'paid': '#28a745',       # Vert
            'cancelled': '#6c757d',  # Gris
            'cancelled_by_credit_note': '#6c757d',  # Gris
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_colored.short_description = 'Statut'
    
    def validate_invoices(self, request, queryset):
        """Action pour valider des factures en lot"""
        validated = 0
        for invoice in queryset:
            if invoice.status == 'draft':
                try:
                    invoice.validate_and_send()
                    validated += 1
                except ValueError:
                    pass
        
        self.message_user(
            request,
            f"{validated} facture(s) validée(s) avec succès."
        )
    validate_invoices.short_description = "Valider les factures sélectionnées"
    
    def mark_as_paid(self, request, queryset):
        """Action pour marquer des factures comme payées"""
        updated = queryset.filter(
            status__in=['sent', 'partially_paid', 'overdue']
        ).update(
            status='paid',
            paid_amount=models.F('total_ttc'),
            remaining_amount=0
        )
        
        self.message_user(
            request,
            f"{updated} facture(s) marquée(s) comme payée(s)."
        )
    mark_as_paid.short_description = "Marquer comme payées"


@admin.register(InvoiceItem)
class InvoiceItemAdmin(admin.ModelAdmin):
    """Administration des éléments de facture"""
    
    list_display = [
        'invoice', 'type', 'position', 'designation', 'quantity',
        'unit_price', 'discount', 'total_ht', 'total_ttc'
    ]
    
    list_filter = ['type', 'vat_rate']
    
    search_fields = [
        'designation', 'description', 'reference', 'invoice__number'
    ]
    
    readonly_fields = ['total_ht', 'total_ttc']
    
    fieldsets = (
        ('Facture', {
            'fields': ('invoice',)
        }),
        ('Type et position', {
            'fields': ('type', 'parent', 'position')
        }),
        ('Contenu', {
            'fields': (
                'reference', 'designation', 'description', 'work_id'
            )
        }),
        ('Quantités et prix', {
            'fields': (
                'quantity', 'unit', 'unit_price', 'discount', 'vat_rate'
            )
        }),
        ('Totaux calculés', {
            'fields': ('total_ht', 'total_ttc'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('invoice')


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    """Administration des paiements"""
    
    list_display = [
        'invoice', 'date', 'amount', 'method', 'reference', 'created_at'
    ]
    
    list_filter = ['method', 'date', 'created_at']
    
    search_fields = [
        'invoice__number', 'invoice__client_name', 'reference', 'notes'
    ]
    
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Paiement', {
            'fields': ('invoice', 'date', 'amount', 'method')
        }),
        ('Références', {
            'fields': ('reference', 'notes')
        }),
        ('Métadonnées', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('invoice')


# Configuration du site admin
admin.site.site_header = "ERP BTP - Administration"
admin.site.site_title = "ERP BTP Admin"
admin.site.index_title = "Administration du système"
