from django.db import models

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
    moved_at = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField(null=True, blank=True)  # Date de fin d'affectation
    notes = models.TextField(blank=True)
    reservation = models.ForeignKey(
        'EquipmentReservation',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='movements',
        help_text="Réservation à l'origine de cette affectation, si applicable."
    )

    def __str__(self):
        return f"{self.equipment} : {self.from_location} → {self.to_location} le {self.moved_at.strftime('%Y-%m-%d %H:%M')}"

class EquipmentReservation(models.Model):
    STATUS_CHOICES = [
        ("RESERVED", "Réservé"),
        ("CANCELLED", "Annulée"),
        ("EXPIRED", "Expirée"),
        ("FULFILLED", "Transformée en affectation"),
    ]
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, related_name="reservations")
    context_id = models.CharField(max_length=100, help_text="Ex: chantier_X_task_123 ou autre identifiant métier")
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="RESERVED")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True)
    fulfilled_movement = models.OneToOneField(
        'EquipmentMovement',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='fulfilled_reservation',
        help_text="Affectation concrétisant cette réservation, si applicable."
    )

    class Meta:
        unique_together = ("equipment", "start_date", "end_date")
        ordering = ["start_date"]

    def __str__(self):
        return f"Réservation de {self.equipment} du {self.start_date.strftime('%Y-%m-%d %H:%M')} au {self.end_date.strftime('%Y-%m-%d %H:%M')} (statut: {self.status})"