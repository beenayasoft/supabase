from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers
from .views import DevisViewSet, LotViewSet, LigneDevisViewSet, DevisLineViewSet

# Créer un routeur pour enregistrer nos ViewSets
router = DefaultRouter()
router.register(r'devis', DevisViewSet)
router.register(r'lots', LotViewSet)
router.register(r'lignes', LigneDevisViewSet)

# Créer un routeur imbriqué pour les lignes de devis
devis_router = routers.NestedSimpleRouter(router, r'devis', lookup='devis')
devis_router.register(r'lines', DevisLineViewSet, basename='devis-lines')

# Les URLs de l'API
urlpatterns = [
    path('', include(router.urls)),
    path('', include(devis_router.urls)),
] 