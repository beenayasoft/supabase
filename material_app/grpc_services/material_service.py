from django_socio_grpc import generics
from material_app.models import Equipment, EquipmentMovement, MaintenancePlan, MaintenanceLog
from material_app.serializers import EquipmentMovementProtoSerializer, MaintenancePlanProtoSerializer, MaintenanceLogProtoSerializer
from material_app.services import is_equipment_available_for_movement
from asgiref.sync import sync_to_async
import grpc

class EquipmentMovementService(generics.AsyncModelService):
    queryset = EquipmentMovement.objects.all()
    serializer_class = EquipmentMovementProtoSerializer

    async def Create(self, request, context):
        equipment = await sync_to_async(Equipment.objects.get)(pk=request.equipment)
        start_date = request.start_date
        end_date = request.end_date
        is_available = await sync_to_async(is_equipment_available_for_movement)(equipment, start_date, end_date)
        if not is_available:
            context.abort(grpc.StatusCode.FAILED_PRECONDITION, "L'équipement n'est pas disponible sur cette période.")
        return await super().Create(request, context)

class MaintenancePlanService(generics.AsyncModelService):
    queryset = MaintenancePlan.objects.all()
    serializer_class = MaintenancePlanProtoSerializer

class MaintenanceLogService(generics.AsyncModelService):
    queryset = MaintenanceLog.objects.all()
    serializer_class = MaintenanceLogProtoSerializer
