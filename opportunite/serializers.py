from rest_framework import serializers
from django.utils import timezone
from .models import Opportunity, OpportunityStatus, OpportunitySource, LossReason
from tiers.models import Tiers


class OpportunitySerializer(serializers.ModelSerializer):
    """Serializer principal pour les opportunités avec logique métier"""
    
    # Champs compatibles backend
    tier_name = serializers.CharField(source='tier.nom', read_only=True)
    tier_type = serializers.CharField(source='tier.type', read_only=True)
    days_open = serializers.SerializerMethodField()
    can_create_quote = serializers.SerializerMethodField()
    stage_display = serializers.CharField(source='get_stage_display', read_only=True)
    source_display = serializers.CharField(source='get_source_display', read_only=True)
    loss_reason_display = serializers.CharField(source='get_loss_reason_display', read_only=True)
    
    # 🚀 Alias compatibles frontend (pour faciliter l'intégration)
    tierId = serializers.CharField(source='tier.id', read_only=True)
    tierName = serializers.CharField(source='tier.nom', read_only=True)
    tierType = serializers.SerializerMethodField()
    estimatedAmount = serializers.DecimalField(source='estimated_amount', max_digits=12, decimal_places=2, required=False)
    expectedCloseDate = serializers.DateField(source='expected_close_date', required=False)
    assignedTo = serializers.CharField(source='assigned_to', required=False, allow_blank=True)
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    updatedAt = serializers.DateTimeField(source='updated_at', read_only=True)
    closedAt = serializers.DateTimeField(source='closed_at', read_only=True)
    lossReason = serializers.CharField(source='loss_reason', required=False, allow_blank=True)
    lossDescription = serializers.CharField(source='loss_description', required=False, allow_blank=True)
    projectId = serializers.CharField(source='project_id', required=False, allow_blank=True)
    
    class Meta:
        model = Opportunity
        fields = [
            # Champs backend originaux
            'id', 'name', 'tier', 'tier_name', 'tier_type', 'stage', 'stage_display',
            'estimated_amount', 'probability', 'expected_close_date', 'source', 
            'source_display', 'description', 'assigned_to', 'created_at', 
            'updated_at', 'closed_at', 'loss_reason', 'loss_reason_display', 
            'loss_description', 'project_id', 'days_open', 'can_create_quote',
            # Alias frontend compatibles
            'tierId', 'tierName', 'tierType', 'estimatedAmount', 'expectedCloseDate',
            'assignedTo', 'createdAt', 'updatedAt', 'closedAt', 'lossReason',
            'lossDescription', 'projectId'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'closed_at', 'probability']
    
    def get_days_open(self, obj):
        """Calcule le nombre de jours depuis l'ouverture"""
        if obj.closed_at:
            return (obj.closed_at.date() - obj.created_at.date()).days
        return (timezone.now().date() - obj.created_at.date()).days
    
    def get_can_create_quote(self, obj):
        """Indique si un devis peut être créé depuis cette opportunité"""
        return obj.stage in [OpportunityStatus.NEEDS_ANALYSIS, OpportunityStatus.NEGOTIATION]
    
    def get_tierType(self, obj):
        """Retourne le type de tier sous forme de liste pour compatibilité frontend"""
        if obj.tier and obj.tier.relation:
            return [obj.tier.relation]
        return ['prospect']
    
    def validate(self, data):
        """Validation métier"""
        # Vérification des champs requis pour les opportunités perdues
        if data.get('stage') == OpportunityStatus.LOST:
            if not data.get('loss_reason'):
                raise serializers.ValidationError({
                    'loss_reason': 'La raison de perte est obligatoire pour une opportunité perdue.'
                })
        
        # Vérification de la date de clôture
        expected_close_date = data.get('expected_close_date')
        if expected_close_date and expected_close_date < timezone.now().date():
            if data.get('stage') not in [OpportunityStatus.WON, OpportunityStatus.LOST]:
                raise serializers.ValidationError({
                    'expected_close_date': 'La date de clôture ne peut pas être dans le passé pour une opportunité active.'
                })
        
        return data


class OpportunityListSerializer(serializers.ModelSerializer):
    """Serializer optimisé pour les listes d'opportunités"""
    
    tier_name = serializers.CharField(source='tier.nom', read_only=True)
    tier_type = serializers.CharField(source='tier.type', read_only=True)
    stage_display = serializers.CharField(source='get_stage_display', read_only=True)
    days_open = serializers.SerializerMethodField()
    
    class Meta:
        model = Opportunity
        fields = [
            'id', 'name', 'tier_name', 'tier_type', 'stage', 'stage_display',
            'estimated_amount', 'probability', 'expected_close_date', 
            'created_at', 'days_open'
        ]
    
    def get_days_open(self, obj):
        if obj.closed_at:
            return (obj.closed_at.date() - obj.created_at.date()).days
        return (timezone.now().date() - obj.created_at.date()).days


class OpportunityKanbanSerializer(serializers.ModelSerializer):
    """Serializer spécialisé pour la vue Kanban"""
    
    # Champs backend
    tier_name = serializers.CharField(source='tier.nom', read_only=True)
    tier_email = serializers.SerializerMethodField()
    tier_telephone = serializers.SerializerMethodField()
    days_open = serializers.SerializerMethodField()
    
    # Alias frontend compatibles
    tierId = serializers.CharField(source='tier.id', read_only=True)
    tierName = serializers.CharField(source='tier.nom', read_only=True)
    tierType = serializers.SerializerMethodField()
    estimatedAmount = serializers.DecimalField(source='estimated_amount', max_digits=12, decimal_places=2)
    expectedCloseDate = serializers.DateField(source='expected_close_date')
    assignedTo = serializers.CharField(source='assigned_to', allow_blank=True)
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    
    class Meta:
        model = Opportunity
        fields = [
            # Champs backend
            'id', 'name', 'tier', 'tier_name', 'tier_email', 'tier_telephone',
            'stage', 'estimated_amount', 'probability', 'expected_close_date',
            'description', 'assigned_to', 'created_at', 'days_open',
            # Alias frontend
            'tierId', 'tierName', 'tierType', 'estimatedAmount', 'expectedCloseDate',
            'assignedTo', 'createdAt'
        ]
    
    def get_tierType(self, obj):
        """Retourne le type de tier sous forme de liste pour compatibilité frontend"""
        if obj.tier and obj.tier.relation:
            return [obj.tier.relation]
        return ['prospect']
    
    def get_days_open(self, obj):
        if obj.closed_at:
            return (obj.closed_at.date() - obj.created_at.date()).days
        return (timezone.now().date() - obj.created_at.date()).days
    
    def get_tier_email(self, obj):
        """Récupère l'email du contact principal ou le premier contact"""
        if obj.tier and obj.tier.contacts.exists():
            contact = obj.tier.contacts.filter(contact_principal_devis=True).first()
            if not contact:
                contact = obj.tier.contacts.first()
            return contact.email if contact else ''
        return ''
    
    def get_tier_telephone(self, obj):
        """Récupère le téléphone du contact principal ou le premier contact"""
        if obj.tier and obj.tier.contacts.exists():
            contact = obj.tier.contacts.filter(contact_principal_devis=True).first()
            if not contact:
                contact = obj.tier.contacts.first()
            return contact.telephone if contact else ''
        return ''


class OpportunityStageUpdateSerializer(serializers.ModelSerializer):
    """Serializer pour les mises à jour de statut avec validation métier"""
    
    class Meta:
        model = Opportunity
        fields = ['stage', 'loss_reason', 'loss_description', 'project_id']
    
    def validate(self, data):
        stage = data.get('stage')
        
        if stage == OpportunityStatus.LOST:
            if not data.get('loss_reason'):
                raise serializers.ValidationError({
                    'loss_reason': 'La raison de perte est obligatoire.'
                })
        
        if stage == OpportunityStatus.WON:
            if not data.get('project_id'):
                # Générer automatiquement un ID de projet si pas fourni
                data['project_id'] = f"PROJ-{timezone.now().strftime('%Y%m%d')}-{self.instance.id.hex[:8]}"
        
        return data


class OpportunityCreateQuoteSerializer(serializers.Serializer):
    """Serializer pour la création de devis depuis une opportunité"""
    
    title = serializers.CharField(max_length=200, required=False)
    description = serializers.CharField(required=False, allow_blank=True)
    notes_internes = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, data):
        # Récupérer l'opportunité depuis le contexte
        opportunity = self.context.get('opportunity')
        if not opportunity:
            raise serializers.ValidationError("Opportunité non trouvée.")
        
        if opportunity.stage not in [OpportunityStatus.NEEDS_ANALYSIS, OpportunityStatus.NEGOTIATION]:
            raise serializers.ValidationError(
                "Un devis ne peut être créé que pour les opportunités en analyse ou négociation."
            )
        
        return data 