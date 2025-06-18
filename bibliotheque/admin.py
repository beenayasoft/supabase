from django.contrib import admin
from .models import Categorie

@admin.register(Categorie)
class CategorieAdmin(admin.ModelAdmin):
    list_display = ('nom', 'parent', 'chemin_complet')
    list_filter = ('parent',)
    search_fields = ('nom',)
    ordering = ('nom',)
