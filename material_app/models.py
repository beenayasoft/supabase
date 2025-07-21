from django.db import models
import uuid
from django.conf import settings

class EquipmentCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class Equipment(models.Model):
    name = models.CharField(max_length=100)
    category = models.ForeignKey(EquipmentCategory, on_delete=models.CASCADE, related_name='equipments')
    serial_number = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.serial_number})"

class EquipmentMovement(models.Model):
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, related_name='movements')
    from_location = models.CharField(max_length=100)
    to_location = models.CharField(max_length=100)
    start_date = models.DateTimeField()  # Date de début d'affectation
    end_date = models.DateTimeField(null=True, blank=True)  # Date de fin d'affectation
    notes = models.TextField(blank=True)
    #moved_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.equipment} : {self.from_location} → {self.to_location} du {self.start_date.strftime('%Y-%m-%d %H:%M')} au {self.end_date.strftime('%Y-%m-%d %H:%M') if self.end_date else '...'}"

class MaintenancePlan(models.Model):
    TYPE_CHOICES = [
        ('TIME_BASED', 'Calendaire'),
        ('USAGE_BASED', 'Compteur d\'heures'),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    equipment = models.ForeignKey('Equipment', on_delete=models.CASCADE, related_name='maintenance_plans')
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    frequency_in_months = models.PositiveIntegerField(null=True, blank=True)
    next_due_date = models.DateField(null=True, blank=True)
    hour_counter_threshold = models.PositiveIntegerField(null=True, blank=True)
    last_maintenance_hours = models.PositiveIntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.get_type_display()}) - {self.equipment}"

class MaintenanceLog(models.Model):
    INTERVENTION_TYPE_CHOICES = [
        ('PREVENTIVE', 'Préventive'),
        ('CURATIVE', 'Curative'),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    equipment = models.ForeignKey('Equipment', on_delete=models.CASCADE, related_name='maintenance_logs')
    maintenance_plan = models.ForeignKey(MaintenancePlan, on_delete=models.SET_NULL, null=True, blank=True, related_name='logs')
    intervention_type = models.CharField(max_length=20, choices=INTERVENTION_TYPE_CHOICES)
    date = models.DateField()
    description = models.TextField()
    hour_counter_at_maintenance = models.PositiveIntegerField(null=True, blank=True)
    cost_parts = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    cost_labor = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    performed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    document_id = models.PositiveIntegerField(null=True, blank=True)  # FK vers GED_Document, à adapter

    def __str__(self):
        return f"{self.get_intervention_type_display()} {self.equipment} le {self.date}"