from django.contrib import admin
from .models import Ouvrage

@admin.register(Ouvrage)
class OuvrageAdmin(admin.ModelAdmin):
    list_display = ('id', 'nom') 