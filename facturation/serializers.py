from rest_framework import serializers
from .models import Facture, LigneFacture, PaiementFacture

class LigneFactureSerializer(serializers.ModelSerializer):
    class Meta:
        model = LigneFacture
        fields = '__all__'

class PaiementFactureSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaiementFacture
        fields = '__all__'

class FactureSerializer(serializers.ModelSerializer):
    lignes = LigneFactureSerializer(many=True, read_only=True)
    paiements = PaiementFactureSerializer(many=True, read_only=True)
    class Meta:
        model = Facture
        fields = '__all__'
        read_only_fields = ('total_ht', 'montant_payé', 'reste_a_payer', 'created_at', 'updated_at')