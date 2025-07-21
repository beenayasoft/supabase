from rest_framework import serializers
from .models import (
    EquipmentCategory, Equipment, EquipmentMovement,
    MaintenancePlan, MaintenanceLog
)

class EquipmentCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = EquipmentCategory
        fields = '__all__'

class EquipmentSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    class Meta:
        model = Equipment
        fields = [
            'id', 'name', 'category', 'category_name', 'serial_number', 'description', 'is_available'
        ]

class EquipmentMovementSerializer(serializers.ModelSerializer):
    equipment_name = serializers.CharField(source='equipment.name', read_only=True)
    
    class Meta:
        model = EquipmentMovement
        fields = [
            'id', 'equipment', 'equipment_name', 'from_location', 'to_location',
            'start_date', 'end_date', 'notes'
        ]
    
    def validate(self, attrs):
        from .services import is_equipment_available_for_movement
        equipment = attrs.get('equipment')
        start_date = attrs.get('start_date')
        end_date = attrs.get('end_date')
        instance = self.instance
        exclude_id = instance.pk if instance else None
        
        if equipment and start_date and end_date:
            if not is_equipment_available_for_movement(equipment, start_date, end_date, exclude_movement_id=exclude_id):
                raise serializers.ValidationError({
                    "non_field_errors": ["L'équipement n'est pas disponible sur cette période."]
                })
        return attrs

class MaintenancePlanSerializer(serializers.ModelSerializer):
    equipment_name = serializers.CharField(source='equipment.name', read_only=True)
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    
    class Meta:
        model = MaintenancePlan
        fields = [
            'id', 'equipment', 'equipment_name', 'name', 'type', 'type_display',
            'frequency_in_months', 'next_due_date', 'hour_counter_threshold',
            'last_maintenance_hours', 'is_active'
        ]

class MaintenanceLogSerializer(serializers.ModelSerializer):
    equipment_name = serializers.CharField(source='equipment.name', read_only=True)
    maintenance_plan_name = serializers.CharField(source='maintenance_plan.name', read_only=True)
    intervention_type_display = serializers.CharField(source='get_intervention_type_display', read_only=True)
    performed_by_username = serializers.CharField(source='performed_by.username', read_only=True)
    total_cost = serializers.SerializerMethodField()
    
    class Meta:
        model = MaintenanceLog
        fields = [
            'id', 'equipment', 'equipment_name', 'maintenance_plan',
            'maintenance_plan_name', 'intervention_type', 'intervention_type_display',
            'date', 'description', 'hour_counter_at_maintenance',
            'cost_parts', 'cost_labor', 'total_cost', 'performed_by',
            'performed_by_username', 'document_id'
        ]
    
    def get_total_cost(self, obj):
        """Calcule le coût total (pièces + main d'œuvre)"""
        return float(obj.cost_parts or 0) + float(obj.cost_labor or 0) 