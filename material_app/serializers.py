from django_socio_grpc import proto_serializers
from .models import EquipmentCategory, Equipment, EquipmentMovement, EquipmentReservation
from .grpc.material_app_pb2 import (
    EquipmentCategoryResponse, EquipmentCategoryListResponse,
    EquipmentResponse, EquipmentListResponse,
    EquipmentMovementResponse, EquipmentMovementListResponse,
)
from material_app.grpc.material_app_pb2 import (
    EquipmentReservationResponse,
    EquipmentReservationListResponse,
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

class EquipmentReservationProtoSerializer(proto_serializers.ModelProtoSerializer):
    class Meta:
        model = EquipmentReservation
        fields = "__all__"
        proto_class = EquipmentReservationResponse
        proto_class_list = EquipmentReservationListResponse
        