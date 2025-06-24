from rest_framework import serializers
from .models import Ouvrage

class OuvrageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ouvrage
        fields = '__all__' 