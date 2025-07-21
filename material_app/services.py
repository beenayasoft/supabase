from django_socio_grpc import generics
from .models import EquipmentCategory, Equipment, EquipmentMovement, MaintenancePlan, MaintenanceLog
from .serializers import EquipmentCategoryProtoSerializer, EquipmentProtoSerializer, EquipmentMovementProtoSerializer, MaintenancePlanProtoSerializer, MaintenanceLogProtoSerializer
from django.db import transaction
from django.utils import timezone
from django.db.models import Q


class EquipmentCategoryService(generics.AsyncModelService):
    queryset = EquipmentCategory.objects.all()
    serializer_class = EquipmentCategoryProtoSerializer

class EquipmentService(generics.AsyncModelService):
    queryset = Equipment.objects.all()
    serializer_class = EquipmentProtoSerializer

class EquipmentMovementService(generics.AsyncModelService):
    queryset = EquipmentMovement.objects.all()
    serializer_class = EquipmentMovementProtoSerializer

class MaintenancePlanService(generics.AsyncModelService):
    queryset = MaintenancePlan.objects.all()
    serializer_class = MaintenancePlanProtoSerializer

class MaintenanceLogService(generics.AsyncModelService):
    queryset = MaintenanceLog.objects.all()
    serializer_class = MaintenanceLogProtoSerializer

def is_equipment_available_for_movement(equipment, start_date, end_date, exclude_movement_id=None):
    qs = EquipmentMovement.objects.filter(
        equipment=equipment,
        start_date__lt=end_date,
        end_date__gt=start_date
    )
    if exclude_movement_id:
        qs = qs.exclude(pk=exclude_movement_id)
    return not qs.exists() 