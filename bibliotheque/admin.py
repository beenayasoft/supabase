from django.contrib import admin
from .models import Categorie, Fourniture, MainOeuvre, Ouvrage, IngredientOuvrage

@admin.register(Categorie)
class CategorieAdmin(admin.ModelAdmin):
    list_display = ('nom', 'parent', 'chemin_complet')
    list_filter = ('parent',)
    search_fields = ('nom',)
    ordering = ('nom',)

@admin.register(Fourniture)
class FournitureAdmin(admin.ModelAdmin):
    list_display = ('nom', 'unite', 'prix_achat_ht', 'categorie', 'reference')
    list_filter = ('categorie', 'unite')
    search_fields = ('nom', 'description', 'reference')
    ordering = ('nom',)

@admin.register(MainOeuvre)
class MainOeuvreAdmin(admin.ModelAdmin):
    list_display = ('nom', 'cout_horaire', 'categorie')
    list_filter = ('categorie',)
    search_fields = ('nom', 'description')
    ordering = ('nom',)

class IngredientOuvrageInline(admin.TabularInline):
    model = IngredientOuvrage
    extra = 1
    fields = ('element_type', 'element_id', 'quantite')
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "element_type":
            from django.contrib.contenttypes.models import ContentType
            kwargs["queryset"] = ContentType.objects.filter(
                model__in=['fourniture', 'mainoeuvre']
            )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

@admin.register(Ouvrage)
class OuvrageAdmin(admin.ModelAdmin):
    list_display = ('nom', 'unite', 'categorie', 'code', 'get_debourse_sec')
    list_filter = ('categorie', 'unite')
    search_fields = ('nom', 'description', 'code')
    ordering = ('nom',)
    inlines = [IngredientOuvrageInline]
    
    def get_debourse_sec(self, obj):
        return obj.debourse_sec
    get_debourse_sec.short_description = "Déboursé sec"

@admin.register(IngredientOuvrage)
class IngredientOuvrageAdmin(admin.ModelAdmin):
    list_display = ('ouvrage', 'get_element_nom', 'get_element_type', 'quantite', 'get_cout_total')
    list_filter = ('ouvrage', 'element_type')
    search_fields = ('ouvrage__nom',)
    
    def get_element_nom(self, obj):
        if obj.element_type.model == 'fourniture':
            try:
                from .models import Fourniture
                return Fourniture.objects.get(id=obj.element_id).nom
            except Fourniture.DoesNotExist:
                return f"Fourniture #{obj.element_id} (non trouvée)"
        elif obj.element_type.model == 'mainoeuvre':
            try:
                from .models import MainOeuvre
                return MainOeuvre.objects.get(id=obj.element_id).nom
            except MainOeuvre.DoesNotExist:
                return f"Main d'œuvre #{obj.element_id} (non trouvée)"
        return f"Élément inconnu ({obj.element_type.model})"
    get_element_nom.short_description = "Élément"
    
    def get_element_type(self, obj):
        return obj.element_type.model
    get_element_type.short_description = "Type d'élément"
    
    def get_cout_total(self, obj):
        return obj.cout_total
    get_cout_total.short_description = "Coût total"
