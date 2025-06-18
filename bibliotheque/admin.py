from django.contrib import admin
from .models import Categorie, Fourniture, MainOeuvre

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
