from django.contrib import admin
from .models import Quote, QuoteItem

class QuoteItemInline(admin.TabularInline):
    """Inline pour gérer les éléments de devis"""
    model = QuoteItem
    extra = 1
    fields = [
        'position', 'type', 'reference', 'designation', 
        'quantity', 'unit', 'unit_price', 'discount', 
        'vat_rate', 'total_ht', 'total_ttc'
    ]
    readonly_fields = ['total_ht', 'total_ttc']
    ordering = ['position']

@admin.register(Quote)
class QuoteAdmin(admin.ModelAdmin):
    """Administration des devis"""
    
    list_display = [
        'number', 'client_name', 'status', 'total_ttc', 
        'issue_date', 'expiry_date', 'created_at'
    ]
    list_filter = ['status', 'issue_date', 'created_at']
    search_fields = ['number', 'client_name', 'project_name']
    readonly_fields = ['number', 'total_ht', 'total_vat', 'total_ttc', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('number', 'status', 'tier')
        }),
        ('Client et projet', {
            'fields': ('client_name', 'client_address', 'project_name', 'project_address')
        }),
        ('Dates', {
            'fields': ('issue_date', 'expiry_date', 'validity_period')
        }),
        ('Contenu', {
            'fields': ('notes', 'terms_and_conditions')
        }),
        ('Totaux', {
            'fields': ('total_ht', 'total_vat', 'total_ttc'),
            'classes': ('collapse',)
        }),
        ('Métadonnées', {
            'fields': ('created_by', 'updated_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [QuoteItemInline]
    
    actions = ['mark_as_sent', 'mark_as_accepted', 'mark_as_rejected']
    
    def mark_as_sent(self, request, queryset):
        """Action pour marquer les devis comme envoyés"""
        updated = 0
        for quote in queryset:
            quote.mark_as_sent()
            updated += 1
        self.message_user(request, f'{updated} devis marqué(s) comme envoyé(s).')
    mark_as_sent.short_description = "Marquer comme envoyé"
    
    def mark_as_accepted(self, request, queryset):
        """Action pour marquer les devis comme acceptés"""
        updated = 0
        for quote in queryset:
            quote.mark_as_accepted()
            updated += 1
        self.message_user(request, f'{updated} devis marqué(s) comme accepté(s).')
    mark_as_accepted.short_description = "Marquer comme accepté"
    
    def mark_as_rejected(self, request, queryset):
        """Action pour marquer les devis comme refusés"""
        updated = 0
        for quote in queryset:
            quote.mark_as_rejected()
            updated += 1
        self.message_user(request, f'{updated} devis marqué(s) comme refusé(s).')
    mark_as_rejected.short_description = "Marquer comme refusé"

@admin.register(QuoteItem)
class QuoteItemAdmin(admin.ModelAdmin):
    """Administration des éléments de devis"""
    
    list_display = [
        'quote', 'position', 'type', 'designation', 
        'quantity', 'unit_price', 'total_ht'
    ]
    list_filter = ['type', 'quote__status']
    search_fields = ['designation', 'reference', 'quote__number']
    readonly_fields = ['total_ht', 'total_ttc']
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('quote', 'type', 'parent', 'position')
        }),
        ('Détails', {
            'fields': ('reference', 'designation', 'description', 'work_id')
        }),
        ('Prix et quantités', {
            'fields': ('quantity', 'unit', 'unit_price', 'discount', 'vat_rate', 'margin')
        }),
        ('Totaux', {
            'fields': ('total_ht', 'total_ttc'),
            'classes': ('collapse',)
        }),
    )
