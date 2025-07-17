from django_socio_grpc import generics
from material_app.models import EquipmentReservation, Equipment, EquipmentMovement
from material_app.serializers import EquipmentReservationProtoSerializer, EquipmentMovementProtoSerializer
from material_app.services import create_reservation, fulfill_reservation, is_equipment_available
from asgiref.sync import sync_to_async

class EquipmentReservationService(generics.AsyncModelService):
    queryset = EquipmentReservation.objects.all()
    serializer_class = EquipmentReservationProtoSerializer

    async def Create(self, request, context):
        equipment = await sync_to_async(Equipment.objects.get)(pk=request.equipment)
        reservation = await sync_to_async(create_reservation)(
            equipment=equipment,
            context_id=request.context_id,
            start_date=request.start_date,
            end_date=request.end_date,
            notes=getattr(request, "notes", "")
        )
        #return self.serializer_class(reservation)
        serializer = self.serializer_class(reservation)
        return serializer.message

    async def Fulfill(self, request, context):
        reservation = await sync_to_async(EquipmentReservation.objects.get)(pk=request.reservation_id)
        movement = await sync_to_async(fulfill_reservation)(
            equipment=reservation.equipment,  # On prend l’équipement de la réservation
            reservation=reservation,
            from_location=request.from_location,
            to_location=request.to_location,
            end_date=reservation.end_date,
            notes=getattr(request, "notes", "")
        )
        #return EquipmentMovementProtoSerializer(movement)
        serializer = EquipmentMovementProtoSerializer(movement)
        return serializer.message


    async def CheckAvailability(self, request, context):
        equipment = await sync_to_async(Equipment.objects.get)(pk=request.equipment)
        is_available = await sync_to_async(is_equipment_available)(
            equipment=equipment,
            start_date=request.start_date,
            end_date=request.end_date
        )
        #return {"is_available": is_available}
        return AvailabilityResponse(is_available=is_available)
