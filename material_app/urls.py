from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    EquipmentCategoryViewSet, EquipmentViewSet,
    EquipmentMovementViewSet, MaintenancePlanViewSet,
    MaintenanceLogViewSet
)

# Créer un routeur et enregistrer nos viewsets
router = DefaultRouter()
router.register(r'equipment-categories', EquipmentCategoryViewSet)
router.register(r'equipment', EquipmentViewSet)
router.register(r'equipment-movements', EquipmentMovementViewSet)
router.register(r'maintenance-plans', MaintenancePlanViewSet)
router.register(r'maintenance-logs', MaintenanceLogViewSet)

# Les URLs de l'API sont déterminées automatiquement par le routeur
urlpatterns = [
    path('', include(router.urls)),
] 