from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FactureViewSet, PaiementFactureViewSet, LigneFactureViewSet

router = DefaultRouter()
router.register(r'factures', FactureViewSet, basename='facture')
router.register(r'paiements', PaiementFactureViewSet, basename='paiementfacture')
router.register(r'lignes', LigneFactureViewSet, basename='lignefacture')

urlpatterns = [
    path('', include(router.urls)),
]