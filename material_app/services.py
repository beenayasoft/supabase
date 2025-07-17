from django_socio_grpc import generics
from .models import EquipmentCategory, Equipment, EquipmentMovement
from .serializers import EquipmentCategoryProtoSerializer, EquipmentProtoSerializer, EquipmentMovementProtoSerializer, EquipmentReservationProtoSerializer
from django.db import transaction
from django.utils import timezone
from .models import EquipmentReservation
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
"""
class EquipmentReservationService(generics.AsyncModelService):
    queryset = EquipmentReservation.objects.all()
    serializer_class = EquipmentReservationProtoSerializer
"""
def is_equipment_available(equipment, start_date, end_date):
    # Vérifier les réservations qui se chevauchent
    overlapping_reservations = EquipmentReservation.objects.filter(
        equipment=equipment,
        status='RESERVED',
        start_date__lt=end_date,
        end_date__gt=start_date
    ).exists()
    # Vérifier les affectations (movements) qui se chevauchent
    overlapping_movements = EquipmentMovement.objects.filter(
        equipment=equipment,
        end_date__gt=start_date,
        moved_at__lt=end_date
    ).exists()
    return not (overlapping_reservations or overlapping_movements)


def is_equipment_available_for_movement(equipment, start_date, end_date, exclude_movement_id=None):
    qs = EquipmentMovement.objects.filter(
        equipment=equipment,
        end_date__gt=start_date,
        moved_at__lt=end_date
    )
    if exclude_movement_id:
        qs = qs.exclude(pk=exclude_movement_id)
    return not qs.exists()


def create_reservation(equipment, context_id, start_date, end_date, notes=""):
    if not equipment or (hasattr(equipment, 'id') and equipment.id in (None, 0)):
        raise Exception("Un ID d'équipement valide est requis.")
    if not is_equipment_available(equipment, start_date, end_date):
        raise Exception("L'équipement n'est pas disponible sur cette période.")
    reservation = EquipmentReservation.objects.create(
        equipment=equipment,
        context_id=context_id,
        start_date=start_date,
        end_date=end_date,
        status='RESERVED',
        notes=notes
    )
    return reservation


def fulfill_reservation(reservation, from_location, to_location, end_date, notes=""):
    if not reservation.equipment or (hasattr(reservation.equipment, 'id') and reservation.equipment.id in (None, 0)):
        raise Exception("La réservation n'est pas liée à un équipement valide.")
    if reservation.status != 'RESERVED':
        raise Exception("La réservation n'est pas active.")
    # Vérification de disponibilité sur la période de la réservation
    if not is_equipment_available_for_movement(reservation.equipment, reservation.start_date, end_date):
        raise Exception("L'équipement est déjà affecté sur cette période.")
    with transaction.atomic():
        # Créer le mouvement (affectation)
        movement = EquipmentMovement.objects.create(
            equipment=reservation.equipment,
            from_location=from_location,
            to_location=to_location,
            moved_at=timezone.now(),
            end_date=end_date,
            notes=notes,
            reservation=reservation
        )
        # Lier le mouvement à la réservation
        reservation.fulfilled_movement = movement
        reservation.status = 'FULFILLED'
        reservation.save()
        # Mettre à jour le statut de l’équipement
        reservation.equipment.is_available = False
        reservation.equipment.save()
    return movement 