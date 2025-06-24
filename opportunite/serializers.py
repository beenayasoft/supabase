from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from .models import Opportunity, OpportunityStatus, OpportunitySource, LossReason
from tiers.serializers import TiersListSerializer, TiersDetailSerializer


class OpportunityListSerializer(serializers.ModelSerializer):
    """Serializer pour la liste des opportunités (version allégée)"""
    tier = TiersListSerializer(read_only=True)
    stage_display = serializers.CharField(source='get_stage_display', read_only=True)
    source_display = serializers.CharField(source='get_source_display', read_only=True)
    amount = serializers.DecimalField(
        source='estimated_amount', 
        max_digits=12, 
        decimal_places=2, 
        read_only=True
    )
    
    class Meta:
        model = Opportunity
        fields = [
            'id', 'name', 'tier', 'stage', 'stage_display', 'amount', 'probability',
            'expected_close_date', 'assigned_to', 'source', 'source_display', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class OpportunityDetailSerializer(serializers.ModelSerializer):
    """Serializer pour le détail complet d'une opportunité"""
    tier = TiersDetailSerializer(read_only=True)
    stage_display = serializers.CharField(source='get_stage_display', read_only=True)
    source_display = serializers.CharField(source='get_source_display', read_only=True)
    loss_reason_display = serializers.CharField(source='get_loss_reason_display', read_only=True)
    weighted_amount = serializers.SerializerMethodField()
    tier_contact_principal = serializers.SerializerMethodField()
    tier_adresse_facturation = serializers.SerializerMethodField()
    
    class Meta:
        model = Opportunity
        fields = [
            'id', 'name', 'tier', 'stage', 'stage_display', 'estimated_amount',
            'weighted_amount', 'probability', 'expected_close_date', 'source', 'source_display',
            'description', 'assigned_to', 'loss_reason', 'loss_reason_display',
            'loss_description', 'project_id', 'created_at', 'updated_at', 'closed_at',
            'tier_contact_principal', 'tier_adresse_facturation'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'closed_at']
    
    def get_weighted_amount(self, obj):
        """Calculer le montant pondéré (montant estimé * probabilité)"""
        return (obj.estimated_amount * obj.probability) / 100
        
    def get_tier_contact_principal(self, obj):
        """Récupérer le contact principal pour devis du tier"""
        if not obj.tier:
            return None
            
        contact_principal = obj.tier.contacts.filter(contact_principal_devis=True).first()
        if not contact_principal:
            contact_principal = obj.tier.contacts.first()
            
        if contact_principal:
            return {
                'id': contact_principal.id,
                'nom': contact_principal.nom,
                'prenom': contact_principal.prenom,
                'email': contact_principal.email,
                'telephone': contact_principal.telephone,
                'fonction': contact_principal.fonction
            }
        return None
        
    def get_tier_adresse_facturation(self, obj):
        """Récupérer l'adresse de facturation du tier"""
        if not obj.tier:
            return None
            
        adresse = obj.tier.adresses.filter(facturation=True).first()
        if not adresse:
            adresse = obj.tier.adresses.first()
            
        if adresse:
            return {
                'id': adresse.id,
                'libelle': adresse.libelle,
                'rue': adresse.rue,
                'ville': adresse.ville,
                'code_postal': adresse.code_postal,
                'pays': adresse.pays
            }
        return None


class OpportunityCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer pour la création et mise à jour d'une opportunité"""
    tier_id = serializers.CharField(write_only=True)
    
    class Meta:
        model = Opportunity
        fields = [
            'name', 'tier_id', 'stage', 'estimated_amount', 'expected_close_date',
            'source', 'description', 'assigned_to', 'loss_reason', 'loss_description'
        ]
    
    def validate_tier_id(self, value):
        """Valider que le tier existe"""
        from tiers.models import Tiers
        try:
            Tiers.objects.get(pk=value)
            return value
        except Tiers.DoesNotExist:
            raise serializers.ValidationError(_("Le tiers spécifié n'existe pas."))
    
    def create(self, validated_data):
        """Créer une opportunité en résolvant la référence au tier"""
        from tiers.models import Tiers
        tier_id = validated_data.pop('tier_id')
        tier = Tiers.objects.get(pk=tier_id)
        
        # Mise à jour de la probabilité en fonction du stage
        stage = validated_data.get('stage', OpportunityStatus.NEW)
        if stage == OpportunityStatus.NEW:
            validated_data['probability'] = 10
        elif stage == OpportunityStatus.NEEDS_ANALYSIS:
            validated_data['probability'] = 30
        elif stage == OpportunityStatus.NEGOTIATION:
            validated_data['probability'] = 60
        elif stage == OpportunityStatus.WON:
            validated_data['probability'] = 100
        elif stage == OpportunityStatus.LOST:
            validated_data['probability'] = 0
        
        # Créer l'opportunité
        opportunity = Opportunity.objects.create(tier=tier, **validated_data)
        return opportunity
    
    def update(self, instance, validated_data):
        """Mettre à jour une opportunité en résolvant les références"""
        if 'tier_id' in validated_data:
            from tiers.models import Tiers
            tier_id = validated_data.pop('tier_id')
            tier = Tiers.objects.get(pk=tier_id)
            instance.tier = tier
        
        # Mettre à jour les champs de l'opportunité
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        return instance


class OpportunityPatchSerializer(serializers.ModelSerializer):
    """Serializer pour les mises à jour partielles (par exemple, changement d'étape)"""
    
    class Meta:
        model = Opportunity
        fields = ['stage', 'estimated_amount', 'probability', 'expected_close_date', 
                 'loss_reason', 'loss_description']
        
    def validate(self, data):
        """Validation spécifique pour les mises à jour partielles"""
        # Si on marque comme perdue, vérifier qu'une raison est fournie
        if 'stage' in data and data['stage'] == OpportunityStatus.LOST:
            if 'loss_reason' not in data:
                raise serializers.ValidationError(_("Une raison de perte est requise pour une opportunité perdue."))
        
        return data 