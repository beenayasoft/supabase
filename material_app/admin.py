from django.contrib import admin
from .models import EquipmentCategory, Equipment, EquipmentMovement, MaintenancePlan, MaintenanceLog

@admin.register(EquipmentCategory)
class EquipmentCategoryAdmin(admin.ModelAdmin):
    search_fields = ['name']
    list_display = ['name', 'description']

@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    search_fields = ['name', 'serial_number']
    list_display = ['name', 'serial_number', 'category', 'is_available']
    list_filter = ['category', 'is_available']
    autocomplete_fields = ['category']

@admin.register(EquipmentMovement)
class EquipmentMovementAdmin(admin.ModelAdmin):
    list_display = ['equipment', 'from_location', 'to_location', 'start_date', 'end_date']
    list_filter = ['equipment']
    search_fields = ['from_location', 'to_location', 'equipment__name']
    autocomplete_fields = ['equipment']

@admin.register(MaintenancePlan)
class MaintenancePlanAdmin(admin.ModelAdmin):
    list_display = ['name', 'equipment', 'type', 'frequency_in_months', 'next_due_date', 'hour_counter_threshold', 'is_active']
    list_filter = ['type', 'is_active', 'equipment']
    search_fields = ['name', 'equipment__name']
    autocomplete_fields = ['equipment']
    readonly_fields = ['id']

@admin.register(MaintenanceLog)
class MaintenanceLogAdmin(admin.ModelAdmin):
    list_display = ['equipment', 'maintenance_plan', 'intervention_type', 'date', 'cost_parts', 'cost_labor', 'performed_by']
    list_filter = ['intervention_type', 'equipment', 'maintenance_plan', 'performed_by']
    search_fields = ['description', 'equipment__name', 'maintenance_plan__name']
    autocomplete_fields = ['equipment', 'maintenance_plan', 'performed_by']
    readonly_fields = ['id']