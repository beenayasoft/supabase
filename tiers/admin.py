from django.contrib import admin
from .models import Tiers, Adresse, Contact, ActiviteTiers


class AdresseInline(admin.TabularInline):
    model = Adresse
    extra = 1
    fields = ['libelle', 'rue', 'ville', 'code_postal', 'pays', 'facturation']


class ContactInline(admin.TabularInline):
    model = Contact
    extra = 1
    fields = ['nom', 'prenom', 'fonction', 'email', 'telephone', 'contact_principal_devis', 'contact_principal_facture']


class ActiviteTiersInline(admin.TabularInline):
    model = ActiviteTiers
    extra = 0
    readonly_fields = ['utilisateur', 'date']
    fields = ['type', 'contenu', 'utilisateur', 'date']
    can_delete = False


@admin.register(Tiers)
class TiersAdmin(admin.ModelAdmin):
    list_display = ['nom', 'type', 'get_flags_display', 'assigned_user', 'date_creation', 'is_deleted']
    list_filter = ['type', 'flags', 'assigned_user', 'is_deleted', 'date_creation']
    search_fields = ['nom', 'siret', 'tva']
    readonly_fields = ['id', 'date_creation', 'date_modification', 'date_archivage']
    inlines = [AdresseInline, ContactInline, ActiviteTiersInline]
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('id', 'type', 'nom', 'siret', 'tva')
        }),
        ('Catégorisation', {
            'fields': ('flags', 'assigned_user')
        }),
        ('Gestion du cycle de vie', {
            'fields': ('is_deleted', 'date_creation', 'date_modification', 'date_archivage'),
            'classes': ('collapse',)
        }),
    )
    
    def get_flags_display(self, obj):
        return ', '.join(obj.flags) if obj.flags else '-'
    get_flags_display.short_description = 'Flags'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('assigned_user')


@admin.register(Adresse)
class AdresseAdmin(admin.ModelAdmin):
    list_display = ['tier', 'libelle', 'ville', 'code_postal', 'facturation']
    list_filter = ['facturation', 'pays']
    search_fields = ['tier__nom', 'ville', 'code_postal']


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ['tier', 'nom', 'prenom', 'fonction', 'email', 'contact_principal_devis', 'contact_principal_facture']
    list_filter = ['contact_principal_devis', 'contact_principal_facture']
    search_fields = ['tier__nom', 'nom', 'prenom', 'email']


@admin.register(ActiviteTiers)
class ActiviteTiersAdmin(admin.ModelAdmin):
    list_display = ['tier', 'type', 'utilisateur', 'date', 'contenu_short']
    list_filter = ['type', 'utilisateur', 'date']
    search_fields = ['tier__nom', 'contenu']
    readonly_fields = ['date']
    
    def contenu_short(self, obj):
        return obj.contenu[:50] + '...' if len(obj.contenu) > 50 else obj.contenu
    contenu_short.short_description = 'Contenu'
