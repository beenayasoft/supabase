from rest_framework import serializers
from django.utils import timezone
from decimal import Decimal
from .models import Quote, QuoteItem, QuoteStatus, VATRate
from tiers.models import Tiers
from tiers.serializers import TiersDetailSerializer


class QuoteItemSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour le modèle QuoteItem - CRUD éléments de devis.
    """
    # Champs calculés en lecture seule
    total_ht = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    total_ttc = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    
    # Informations sur le type en lecture seule
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    vat_rate_display = serializers.CharField(source='get_vat_rate_display', read_only=True)
    
    class Meta:
        model = QuoteItem
        fields = [
            'id', 'quote', 'type', 'type_display', 'parent', 'position',
            'reference', 'designation', 'description', 'unit', 'quantity',
            'unit_price', 'discount', 'vat_rate', 'vat_rate_display', 'margin',
            'total_ht', 'total_ttc', 'work_id', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_quantity(self, value):
        """Valider que la quantité est positive."""
        if value <= 0:
            raise serializers.ValidationError("La quantité doit être supérieure à 0.")
        return value
    
    def validate_unit_price(self, value):
        """Valider que le prix unitaire est positif ou nul."""
        if value < 0:
            raise serializers.ValidationError("Le prix unitaire ne peut pas être négatif.")
        return value
    
    def validate_discount(self, value):
        """Valider que la remise est entre 0 et 100%."""
        if value < 0 or value > 100:
            raise serializers.ValidationError("La remise doit être comprise entre 0 et 100%.")
        return value
    
    def validate_margin(self, value):
        """Valider que la marge est positive ou nulle."""
        if value < 0:
            raise serializers.ValidationError("La marge ne peut pas être négative.")
        return value
    
    def validate(self, data):
        """Validation globale des données."""
        # Vérifier la hiérarchie des éléments
        if data.get('parent') and data.get('type') in ['chapter', 'section']:
            raise serializers.ValidationError(
                "Un chapitre ou une section ne peut pas avoir de parent."
            )
        
        # Vérifier que les éléments avec parent ne sont pas des chapitres/sections
        if data.get('parent') and data.get('type') in ['chapter', 'section']:
            raise serializers.ValidationError(
                "Les chapitres et sections ne peuvent pas être des sous-éléments."
            )
        
        return data


class QuoteItemDetailSerializer(QuoteItemSerializer):
    """
    Sérialiseur détaillé pour QuoteItem incluant les relations et sous-éléments.
    """
    # Informations sur l'élément parent
    parent_info = serializers.SerializerMethodField()
    
    # Sous-éléments (pour chapitres et sections)
    children = serializers.SerializerMethodField()
    
    # Informations sur le devis parent
    quote_number = serializers.CharField(source='quote.number', read_only=True)
    
    class Meta(QuoteItemSerializer.Meta):
        fields = QuoteItemSerializer.Meta.fields + [
            'parent_info', 'children', 'quote_number'
        ]
    
    def get_parent_info(self, obj):
        """Récupérer les informations de l'élément parent."""
        if obj.parent:
            return {
                'id': str(obj.parent.id),
                'designation': obj.parent.designation,
                'type': obj.parent.type,
            }
        return None
    
    def get_children(self, obj):
        """Récupérer les sous-éléments."""
        if obj.type in ['chapter', 'section']:
            children = obj.children.all().order_by('position')
            return QuoteItemSerializer(children, many=True).data
        return []


class QuoteSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour le modèle Quote - CRUD devis de base.
    """
    # Informations client en lecture seule
    client_name = serializers.CharField(source='tier.nom', read_only=True)
    client_type = serializers.CharField(source='tier.get_type_display', read_only=True)
    
    # Statuts en lecture seule
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    # Totaux calculés en lecture seule
    total_ht = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    total_vat = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    total_ttc = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    
    # Nombre d'éléments dans le devis
    items_count = serializers.SerializerMethodField()
    
    # Dates formatées
    issue_date_formatted = serializers.SerializerMethodField()
    expiry_date_formatted = serializers.SerializerMethodField()
    
    class Meta:
        model = Quote
        fields = [
            'id', 'number', 'status', 'status_display', 'tier', 
            'client_name', 'client_type', 'client_address',
            'project_name', 'project_address', 'issue_date', 'expiry_date',
            'issue_date_formatted', 'expiry_date_formatted', 'validity_period',
            'notes', 'terms_and_conditions', 'total_ht', 'total_vat', 'total_ttc',
            'items_count', 'created_at', 'updated_at', 'created_by', 'updated_by'
        ]
        read_only_fields = [
            'id', 'number', 'total_ht', 'total_vat', 'total_ttc', 
            'created_at', 'updated_at'
        ]
    
    def get_items_count(self, obj):
        """Compter le nombre d'éléments dans le devis."""
        return obj.items.count()
    
    def get_issue_date_formatted(self, obj):
        """Formater la date d'émission."""
        if obj.issue_date:
            return obj.issue_date.strftime('%d/%m/%Y')
        return None
    
    def get_expiry_date_formatted(self, obj):
        """Formater la date d'expiration."""
        if obj.expiry_date:
            return obj.expiry_date.strftime('%d/%m/%Y')
        return None
    
    def validate_tier(self, value):
        """Valider que le tier existe."""
        if not Tiers.objects.filter(id=value.id).exists():
            raise serializers.ValidationError("Le client spécifié n'existe pas.")
        return value
    
    def validate_validity_period(self, value):
        """Valider la durée de validité."""
        if value <= 0:
            raise serializers.ValidationError("La durée de validité doit être positive.")
        if value > 365:
            raise serializers.ValidationError("La durée de validité ne peut pas dépasser 365 jours.")
        return value
    
    def validate(self, data):
        """Validation globale des données."""
        # Vérifier que la date d'expiration est postérieure à la date d'émission
        issue_date = data.get('issue_date')
        expiry_date = data.get('expiry_date')
        
        if issue_date and expiry_date and expiry_date <= issue_date:
            raise serializers.ValidationError(
                "La date d'expiration doit être postérieure à la date d'émission."
            )
        
        return data
    
    def create(self, validated_data):
        """Créer un nouveau devis avec numérotation automatique."""
        # Générer le numéro de devis automatiquement
        from django.db.models import Max
        import datetime
        
        current_year = datetime.datetime.now().year
        last_quote = Quote.objects.filter(
            number__startswith=f'DEV-{current_year}'
        ).aggregate(Max('number'))
        
        if last_quote['number__max']:
            # Extraire le dernier numéro et incrémenter
            last_number = int(last_quote['number__max'].split('-')[-1])
            new_number = f'DEV-{current_year}-{last_number + 1:03d}'
        else:
            # Premier devis de l'année
            new_number = f'DEV-{current_year}-001'
        
        validated_data['number'] = new_number
        
        # Récupérer les informations du client
        tier = validated_data['tier']
        validated_data['client_name'] = tier.nom
        
        # Récupérer l'adresse principale de facturation ou la première adresse
        billing_address = tier.adresses.filter(facturation=True).first()
        if billing_address:
            validated_data['client_address'] = f"{billing_address.rue}, {billing_address.code_postal} {billing_address.ville}"
        elif tier.adresses.exists():
            first_address = tier.adresses.first()
            validated_data['client_address'] = f"{first_address.rue}, {first_address.code_postal} {first_address.ville}"
        else:
            validated_data['client_address'] = ""
        
        return super().create(validated_data)


class QuoteDetailSerializer(QuoteSerializer):
    """
    Sérialiseur détaillé pour Quote incluant tous les éléments du devis.
    """
    # Informations complètes du client
    tier_details = TiersDetailSerializer(source='tier', read_only=True)
    
    # Tous les éléments du devis organisés hiérarchiquement
    items = serializers.SerializerMethodField()
    
    # Statistiques sur les éléments
    items_stats = serializers.SerializerMethodField()
    
    # Répartition de la TVA
    vat_breakdown = serializers.SerializerMethodField()
    
    class Meta(QuoteSerializer.Meta):
        fields = QuoteSerializer.Meta.fields + [
            'tier_details', 'items', 'items_stats', 'vat_breakdown'
        ]
    
    def get_items(self, obj):
        """Récupérer tous les éléments du devis organisés hiérarchiquement."""
        # Récupérer d'abord les éléments racines (sans parent)
        root_items = obj.items.filter(parent=None).order_by('position')
        
        def serialize_item_with_children(item):
            """Sérialiser un élément avec ses enfants."""
            serialized = QuoteItemSerializer(item).data
            
            # Ajouter les enfants si c'est un chapitre ou une section
            if item.type in ['chapter', 'section']:
                children = item.children.all().order_by('position')
                serialized['children'] = [
                    serialize_item_with_children(child) for child in children
                ]
            
            return serialized
        
        return [serialize_item_with_children(item) for item in root_items]
    
    def get_items_stats(self, obj):
        """Calculer les statistiques sur les éléments."""
        items = obj.items.all()
        
        stats = {
            'total_items': items.count(),
            'chapters': items.filter(type='chapter').count(),
            'sections': items.filter(type='section').count(),
            'products': items.filter(type='product').count(),
            'services': items.filter(type='service').count(),
            'works': items.filter(type='work').count(),
            'discounts': items.filter(type='discount').count(),
        }
        
        return stats
    
    def get_vat_breakdown(self, obj):
        """Calculer la répartition de la TVA."""
        vat_breakdown = {}
        items = obj.items.exclude(type__in=['chapter', 'section'])
        
        for item in items:
            vat_rate = float(item.vat_rate)
            vat_amount = item.total_ttc - item.total_ht
            
            if vat_rate in vat_breakdown:
                vat_breakdown[vat_rate]['base_ht'] += float(item.total_ht)
                vat_breakdown[vat_rate]['vat_amount'] += float(vat_amount)
            else:
                vat_breakdown[vat_rate] = {
                    'rate': vat_rate,
                    'base_ht': float(item.total_ht),
                    'vat_amount': float(vat_amount),
                }
        
        return list(vat_breakdown.values())


class QuoteStatsSerializer(serializers.Serializer):
    """
    Sérialiseur pour les statistiques globales des devis.
    """
    total = serializers.IntegerField()
    draft = serializers.IntegerField()
    sent = serializers.IntegerField()
    accepted = serializers.IntegerField()
    rejected = serializers.IntegerField()
    expired = serializers.IntegerField()
    cancelled = serializers.IntegerField()
    total_amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    acceptance_rate = serializers.DecimalField(max_digits=5, decimal_places=2)


class QuoteActionSerializer(serializers.Serializer):
    """
    Sérialiseur pour les actions sur les devis (envoi, acceptation, etc.).
    """
    action = serializers.ChoiceField(
        choices=['send', 'accept', 'reject', 'cancel'],
        help_text="Action à effectuer sur le devis"
    )
    note = serializers.CharField(
        max_length=500, 
        required=False,
        help_text="Note optionnelle pour l'action"
    )


class QuoteDuplicateSerializer(serializers.Serializer):
    """
    Sérialiseur pour la duplication de devis.
    """
    tier = serializers.PrimaryKeyRelatedField(
        queryset=Tiers.objects.all(),
        required=False,
        help_text="Nouveau client pour le devis dupliqué"
    )
    project_name = serializers.CharField(
        max_length=255,
        required=False,
        help_text="Nouveau nom de projet"
    )
    project_address = serializers.CharField(
        required=False,
        help_text="Nouvelle adresse de projet"
    )
    copy_items = serializers.BooleanField(
        default=True,
        help_text="Copier les éléments du devis original"
    )


class QuoteExportSerializer(serializers.Serializer):
    """
    Sérialiseur pour l'export de devis (PDF, Excel, etc.).
    """
    format = serializers.ChoiceField(
        choices=['pdf', 'excel', 'csv'],
        default='pdf',
        help_text="Format d'export"
    )
    include_details = serializers.BooleanField(
        default=True,
        help_text="Inclure les détails des éléments"
    )
    language = serializers.ChoiceField(
        choices=['fr', 'en', 'ar'],
        default='fr',
        help_text="Langue du document"
    ) 