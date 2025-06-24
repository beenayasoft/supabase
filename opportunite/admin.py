from django.contrib import admin
from .models import Opportunity, OpportunityStatus, OpportunitySource, LossReason

@admin.register(Opportunity)
class OpportunityAdmin(admin.ModelAdmin):
    list_display = ('name', 'tier', 'get_stage_display', 'estimated_amount', 'probability', 'expected_close_date', 'assigned_to')
    list_filter = ('stage', 'source', 'loss_reason')
    search_fields = ('name', 'tier__nom', 'description')
    readonly_fields = ('created_at', 'updated_at', 'closed_at')
    fieldsets = (
        ('Informations principales', {
            'fields': ('name', 'tier', 'description')
        }),
        ('Progression', {
            'fields': ('stage', 'estimated_amount', 'probability', 'expected_close_date')
        }),
        ('Source et attribution', {
            'fields': ('source', 'assigned_to')
        }),
        ('En cas de perte', {
            'fields': ('loss_reason', 'loss_description'),
            'classes': ('collapse',)
        }),
        ('Informations système', {
            'fields': ('project_id', 'created_at', 'updated_at', 'closed_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_stage_display(self, obj):
        return obj.get_stage_display()
    get_stage_display.short_description = 'Étape'
    
    def get_list_display(self, request):
        """Ajouter dynamiquement des champs au list_display selon le contexte"""
        if request.user.is_superuser:
            return self.list_display + ('created_at',)
        return self.list_display
