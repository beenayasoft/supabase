from django_socio_grpc.services.app_handler_registry import AppHandlerRegistry
from .services import EquipmentCategoryService, EquipmentService, EquipmentMovementService
from .grpc_services.material_service import EquipmentReservationService

def grpc_handlers(server):
    app_registry = AppHandlerRegistry("material_app", server)
    app_registry.register(EquipmentCategoryService)
    app_registry.register(EquipmentService)
    app_registry.register(EquipmentMovementService)
    app_registry.register(EquipmentReservationService)
    # Enregistrement explicite du service de réservation
    #EquipmentReservationService.as_servicer()