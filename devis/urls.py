from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DevisViewSet, LotViewSet, LigneDevisViewSet

# Créer un routeur pour enregistrer nos ViewSets
router = DefaultRouter()
router.register(r'devis', DevisViewSet)
router.register(r'lots', LotViewSet)
router.register(r'lignes', LigneDevisViewSet)

# Les URLs de l'API
urlpatterns = [
    path('', include(router.urls)),
] 