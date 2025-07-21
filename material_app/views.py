from rest_framework import viewsets
from .models import (
    EquipmentCategory, Equipment, EquipmentMovement,
    MaintenancePlan, MaintenanceLog
)
from .rest_serializers import (
    EquipmentCategorySerializer, EquipmentSerializer,
    EquipmentMovementSerializer, MaintenancePlanSerializer,
    MaintenanceLogSerializer
)

class EquipmentCategoryViewSet(viewsets.ModelViewSet):
    """
    API endpoint pour gérer les catégories d'équipement.
    Fournit les opérations CRUD complètes.
    """
    queryset = EquipmentCategory.objects.all()
    serializer_class = EquipmentCategorySerializer

class EquipmentViewSet(viewsets.ModelViewSet):
    """
    API endpoint pour gérer les équipements.
    Inclut les informations de catégorie.
    """
    queryset = Equipment.objects.all()
    serializer_class = EquipmentSerializer

class EquipmentMovementViewSet(viewsets.ModelViewSet):
    """
    API endpoint pour gérer les mouvements d'équipement.
    Inclut la validation de disponibilité.
    """
    queryset = EquipmentMovement.objects.all()
    serializer_class = EquipmentMovementSerializer

class MaintenancePlanViewSet(viewsets.ModelViewSet):
    """
    API endpoint pour gérer les plans de maintenance.
    """
    queryset = MaintenancePlan.objects.all()
    serializer_class = MaintenancePlanSerializer

class MaintenanceLogViewSet(viewsets.ModelViewSet):
    """
    API endpoint pour gérer les logs de maintenance.
    Inclut le calcul automatique du coût total.
    """
    queryset = MaintenanceLog.objects.all()
    serializer_class = MaintenanceLogSerializer 