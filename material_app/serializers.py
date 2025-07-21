from django_socio_grpc import proto_serializers
from .models import EquipmentCategory, Equipment, EquipmentMovement, MaintenancePlan, MaintenanceLog
from .grpc.material_app_pb2 import (
    EquipmentCategoryResponse, EquipmentCategoryListResponse,
    EquipmentResponse, EquipmentListResponse,
    EquipmentMovementResponse, EquipmentMovementListResponse,
    MaintenancePlanResponse, MaintenancePlanListResponse,
    MaintenanceLogResponse, MaintenanceLogListResponse
)

class EquipmentCategoryProtoSerializer(proto_serializers.ModelProtoSerializer):
    class Meta:
        model = EquipmentCategory
        fields = "__all__"
        proto_class = EquipmentCategoryResponse
        proto_class_list = EquipmentCategoryListResponse

class EquipmentProtoSerializer(proto_serializers.ModelProtoSerializer):
    class Meta:
        model = Equipment
        fields = "__all__"
        proto_class = EquipmentResponse
        proto_class_list = EquipmentListResponse

class EquipmentMovementProtoSerializer(proto_serializers.ModelProtoSerializer):
    class Meta:
        model = EquipmentMovement
        fields = "__all__"
        proto_class = EquipmentMovementResponse
        proto_class_list = EquipmentMovementListResponse

    def validate(self, attrs):
        from .services import is_equipment_available_for_movement
        equipment = attrs.get('equipment')
        start_date = attrs.get('start_date')
        end_date = attrs.get('end_date')
        instance = getattr(self, 'instance', None)
        exclude_id = instance.pk if instance else None
        if equipment and start_date and end_date:
            if not is_equipment_available_for_movement(equipment, start_date, end_date, exclude_movement_id=exclude_id):
                raise proto_serializers.ValidationError("L'équipement n'est pas disponible sur cette période.")
        return attrs

class MaintenancePlanProtoSerializer(proto_serializers.ModelProtoSerializer):
    class Meta:
        model = MaintenancePlan
        fields = "__all__"
        proto_class = MaintenancePlanResponse
        proto_class_list = MaintenancePlanListResponse

    def validate(self, attrs):
        print("DEBUG type reçu:", repr(attrs.get('type')))
        return super().validate(attrs)

class MaintenanceLogProtoSerializer(proto_serializers.ModelProtoSerializer):
    class Meta:
        model = MaintenanceLog
        fields = "__all__"
        proto_class = MaintenanceLogResponse
        proto_class_list = MaintenanceLogListResponse 
        