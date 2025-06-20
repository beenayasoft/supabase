from django.contrib import admin
from .models import Devis, Lot, LigneDevis

class LigneDevisInline(admin.TabularInline):
    """
    Inline pour afficher les lignes de devis dans l'admin des lots.
    """
    model = LigneDevis
    extra = 0
    fields = ('type', 'ouvrage', 'description', 'quantite', 'unite', 'prix_unitaire', 'debourse', 'ordre')
    ordering = ('ordre',)

class LotInline(admin.TabularInline):
    """
    Inline pour afficher les lots dans l'admin des devis.
    """
    model = Lot
    extra = 0
    fields = ('nom', 'ordre', 'description')
    ordering = ('ordre',)

@admin.register(Lot)
class LotAdmin(admin.ModelAdmin):
    """
    Admin pour le modèle Lot.
    """
    list_display = ('nom', 'devis', 'ordre', 'get_total_ht', 'get_marge')
    list_filter = ('devis',)
    search_fields = ('nom', 'devis__numero', 'devis__objet')
    ordering = ('devis', 'ordre', 'nom')
    inlines = [LigneDevisInline]
    
    def get_total_ht(self, obj):
        return f"{obj.total_ht:.2f} €"
    get_total_ht.short_description = "Total HT"
    
    def get_marge(self, obj):
        return f"{obj.marge:.2f} %"
    get_marge.short_description = "Marge"

@admin.register(Devis)
class DevisAdmin(admin.ModelAdmin):
    """
    Admin pour le modèle Devis.
    """
    list_display = ('numero', 'client', 'objet', 'statut', 'date_creation', 'get_total_ht', 'get_marge_totale')
    list_filter = ('statut', 'date_creation', 'client')
    search_fields = ('numero', 'objet', 'client__nom')
    readonly_fields = ('date_creation',)
    ordering = ('-date_creation', 'numero')
    inlines = [LotInline]
    
    def get_total_ht(self, obj):
        return f"{obj.total_ht:.2f} €"
    get_total_ht.short_description = "Total HT"
    
    def get_marge_totale(self, obj):
        return f"{obj.marge_totale:.2f} %"
    get_marge_totale.short_description = "Marge totale"

@admin.register(LigneDevis)
class LigneDevisAdmin(admin.ModelAdmin):
    """
    Admin pour le modèle LigneDevis.
    """
    list_display = ('description', 'lot', 'type', 'quantite', 'unite', 'prix_unitaire', 'debourse', 'get_total_ht', 'get_marge')
    list_filter = ('lot__devis', 'lot', 'type')
    search_fields = ('description', 'lot__nom', 'lot__devis__numero')
    ordering = ('lot', 'ordre')
    
    def get_total_ht(self, obj):
        return f"{obj.total_ht:.2f} €"
    get_total_ht.short_description = "Total HT"
    
    def get_marge(self, obj):
        return f"{obj.marge:.2f} %"
    get_marge.short_description = "Marge"
