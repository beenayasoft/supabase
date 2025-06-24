from django.contrib import admin
from .models import Facture, LigneFacture, PaiementFacture

class LigneFactureInline(admin.TabularInline):
    model = LigneFacture
    extra = 1

class PaiementFactureInline(admin.TabularInline):
    model = PaiementFacture
    extra = 0

@admin.register(Facture)
class FactureAdmin(admin.ModelAdmin):
    list_display = ('id', 'devis', 'type', 'statut', 'total_ht', 'montant_payé', 'reste_a_payer', 'date_emission')
    list_filter = ('statut', 'type', 'date_emission')
    search_fields = ('devis__id',)
    inlines = [LigneFactureInline, PaiementFactureInline]
    readonly_fields = ('total_ht', 'montant_payé', 'reste_a_payer', 'created_at', 'updated_at')

@admin.register(LigneFacture)
class LigneFactureAdmin(admin.ModelAdmin):
    list_display = ('facture', 'designation', 'quantite', 'prix_unitaire', 'sous_total_ht')

@admin.register(PaiementFacture)
class PaiementFactureAdmin(admin.ModelAdmin):
    list_display = ('facture', 'montant', 'date_paiement', 'moyen', 'reference')