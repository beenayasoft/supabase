from django_socio_grpc.services.app_handler_registry import AppHandlerRegistry
from .services import EquipmentCategoryService, EquipmentService, EquipmentMovementService
from .grpc_services.material_service import MaintenancePlanService, MaintenanceLogService


def grpc_handlers(server):
    app_registry = AppHandlerRegistry("material_app", server)
    app_registry.register(EquipmentCategoryService)
    app_registry.register(EquipmentService)
    app_registry.register(EquipmentMovementService)
    app_registry.register(MaintenancePlanService)
    app_registry.register(MaintenanceLogService)