from django.contrib import admin
from .models import EquipmentCategory, Equipment, EquipmentMovement, EquipmentReservation

admin.site.register(EquipmentCategory)
admin.site.register(Equipment)
admin.site.register(EquipmentMovement)
admin.site.register(EquipmentReservation)