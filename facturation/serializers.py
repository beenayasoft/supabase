from rest_framework import serializers
from decimal import Decimal
from .models import Invoice, InvoiceItem, Payment, InvoiceStatus, VATRate, PaymentMethod


class PaymentSerializer(serializers.ModelSerializer):
    """Serializer pour les paiements - Compatible frontend Payment"""
    
    class Meta:
        model = Payment
        fields = [
            'id', 'invoice', 'date', 'amount', 'method', 
            'reference', 'notes', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def validate_amount(self, value):
        """Valider le montant"""
        if value <= 0:
            raise serializers.ValidationError("Le montant doit être positif")
        return value


class InvoiceItemSerializer(serializers.ModelSerializer):
    """Serializer pour les éléments de facture - Compatible frontend InvoiceItem"""
    
    # Propriété calculée pour compatibilité frontend
    parent_id = serializers.CharField(read_only=True)
    
    class Meta:
        model = InvoiceItem
        fields = [
            'id', 'invoice', 'type', 'parent', 'parent_id', 'position',
            'reference', 'designation', 'description', 'unit',
            'quantity', 'unit_price', 'discount', 'vat_rate',
            'total_ht', 'total_ttc', 'work_id'
        ]
        read_only_fields = ['id', 'parent_id', 'total_ht', 'total_ttc']  # Calculés automatiquement
    
    def validate_quantity(self, value):
        """Valider la quantité"""
        if value < 0:
            raise serializers.ValidationError("La quantité ne peut pas être négative")
        return value
    
    def validate_unit_price(self, value):
        """Valider le prix unitaire"""
        if value < 0:
            raise serializers.ValidationError("Le prix unitaire ne peut pas être négatif")
        return value
    
    def validate_discount(self, value):
        """Valider la remise"""
        if value < 0 or value > 100:
            raise serializers.ValidationError("La remise doit être entre 0 et 100%")
        return value


class InvoiceListSerializer(serializers.ModelSerializer):
    """Serializer simplifié pour la liste des factures"""
    
    class Meta:
        model = Invoice
        fields = [
            'id', 'number', 'status', 'client_name', 'project_name',
            'issue_date', 'due_date', 'total_ht', 'total_vat', 'total_ttc',
            'paid_amount', 'remaining_amount', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class InvoiceDetailSerializer(serializers.ModelSerializer):
    """Serializer complet pour les détails d'une facture - Compatible frontend Invoice"""
    
    # Relations incluses
    items = InvoiceItemSerializer(many=True, read_only=True)
    payments = PaymentSerializer(many=True, read_only=True)
    
    # Champs calculés pour compatibilité frontend
    client_id = serializers.CharField(read_only=True)
    project_id = serializers.CharField(read_only=True)
    quote_id = serializers.CharField(read_only=True)
    credit_note_id = serializers.CharField(read_only=True)
    original_invoice_id = serializers.CharField(read_only=True)
    
    class Meta:
        model = Invoice
        fields = [
            # Identifiants
            'id', 'number', 'status',
            
            # Relations et informations client
            'tier', 'client_id', 'client_name', 'client_address',
            'project_id', 'project_name', 'project_address', 'project_reference',
            
            # Dates
            'issue_date', 'due_date', 'payment_terms',
            
            # Contenu
            'notes', 'terms_and_conditions',
            
            # Montants
            'total_ht', 'total_vat', 'total_ttc', 'paid_amount', 'remaining_amount',
            
            # Liens avec autres documents
            'quote', 'quote_id', 'quote_number', 'credit_note', 'credit_note_id', 
            'original_invoice', 'original_invoice_id',
            
            # Métadonnées
            'created_at', 'updated_at', 'created_by', 'updated_by',
            
            # Relations
            'items', 'payments'
        ]
        read_only_fields = [
            'id', 'client_id', 'project_id', 'quote_id', 'credit_note_id', 'original_invoice_id',
            'total_ht', 'total_vat', 'total_ttc', 'remaining_amount', 'created_at', 'updated_at'
        ]
    
    def validate_due_date(self, value):
        """Valider la date d'échéance"""
        issue_date = self.initial_data.get('issue_date')
        if issue_date and value < issue_date:
            raise serializers.ValidationError("La date d'échéance ne peut pas être antérieure à la date d'émission")
        return value


class InvoiceCreateSerializer(serializers.ModelSerializer):
    """Serializer pour créer une facture - Compatible frontend CreateInvoiceRequest"""
    
    # Relations pour création
    items = InvoiceItemSerializer(many=True, required=False)
    
    class Meta:
        model = Invoice
        fields = [
            'id', 'tier', 'client_name', 'client_address', 'project_name', 
            'project_address', 'project_reference', 'issue_date', 'due_date', 'payment_terms',
            'notes', 'terms_and_conditions', 'quote', 'quote_number',
            'created_by', 'items'
        ]
        read_only_fields = ['id']
    
    def create(self, validated_data):
        """Créer une facture avec ses éléments"""
        items_data = validated_data.pop('items', [])
        
        # Créer la facture
        invoice = Invoice.objects.create(**validated_data)
        
        # Créer les éléments
        for item_data in items_data:
            InvoiceItem.objects.create(invoice=invoice, **item_data)
        
        # Mettre à jour les totaux
        invoice.update_totals()
        
        # S'assurer que l'ID est bien présent
        invoice.refresh_from_db()
        
        return invoice


class InvoiceFromQuoteSerializer(serializers.Serializer):
    """Serializer pour créer une facture depuis un devis - US 5.1"""
    
    quote_id = serializers.UUIDField()
    invoice_type = serializers.ChoiceField(choices=['acompte', 'total'])
    acompte_percentage = serializers.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        required=False,
        min_value=0,
        max_value=100
    )
    client_name = serializers.CharField(max_length=255, required=False)
    client_address = serializers.CharField(required=False)
    project_name = serializers.CharField(max_length=255, required=False)
    project_address = serializers.CharField(required=False)
    project_reference = serializers.CharField(max_length=100, required=False)
    payment_terms = serializers.IntegerField(default=30)
    notes = serializers.CharField(required=False)
    terms_and_conditions = serializers.CharField(required=False)
    
    def validate(self, data):
        """Validation croisée"""
        if data['invoice_type'] == 'acompte' and not data.get('acompte_percentage'):
            raise serializers.ValidationError({
                'acompte_percentage': 'Le pourcentage d\'acompte est requis pour une facture d\'acompte'
            })
        return data


class ValidateInvoiceSerializer(serializers.Serializer):
    """Serializer pour valider et émettre une facture - US 5.3"""
    pass  # Aucun champ requis, l'action est dans la vue


class RecordPaymentSerializer(serializers.Serializer):
    """Serializer pour enregistrer un paiement - US 5.4"""
    
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    method = serializers.ChoiceField(choices=PaymentMethod.choices)
    date = serializers.DateField(required=False)
    reference = serializers.CharField(max_length=100, required=False)
    notes = serializers.CharField(required=False)
    
    def validate_amount(self, value):
        """Valider le montant"""
        if value <= 0:
            raise serializers.ValidationError("Le montant doit être positif")
        return value


class CreateCreditNoteSerializer(serializers.Serializer):
    """Serializer pour créer un avoir - US 5.5"""
    
    reason = serializers.CharField(required=False)
    is_full_credit_note = serializers.BooleanField(default=True)
    selected_items = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        help_text="IDs des éléments à inclure dans l'avoir (requis si is_full_credit_note=false)"
    )
    
    def validate(self, data):
        """Validation croisée"""
        if not data['is_full_credit_note'] and not data.get('selected_items'):
            raise serializers.ValidationError({
                'selected_items': 'Les éléments sélectionnés sont requis pour un avoir partiel'
            })
        return data


class InvoiceStatsSerializer(serializers.Serializer):
    """Serializer pour les statistiques de facturation"""
    
    total_invoices = serializers.IntegerField()
    draft_invoices = serializers.IntegerField()
    sent_invoices = serializers.IntegerField()
    paid_invoices = serializers.IntegerField()
    overdue_invoices = serializers.IntegerField()
    partially_paid_invoices = serializers.IntegerField(default=0)
    cancelled_invoices = serializers.IntegerField(default=0)
    credit_note_invoices = serializers.IntegerField(default=0)
    total_amount_ht = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_amount_ttc = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_paid = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_outstanding = serializers.DecimalField(max_digits=15, decimal_places=2)
    overdue_amount = serializers.DecimalField(max_digits=15, decimal_places=2, default=0)
    average_payment_delay = serializers.FloatField(default=0)


class InvoiceFilterSerializer(serializers.Serializer):
    """Serializer pour les filtres de factures"""
    
    status = serializers.MultipleChoiceField(
        choices=InvoiceStatus.choices,
        required=False
    )
    client_id = serializers.CharField(required=False)
    project_id = serializers.CharField(required=False)
    date_from = serializers.DateField(required=False)
    date_to = serializers.DateField(required=False)
    amount_min = serializers.DecimalField(max_digits=12, decimal_places=2, required=False)
    amount_max = serializers.DecimalField(max_digits=12, decimal_places=2, required=False)
    search = serializers.CharField(required=False)
    
    def validate(self, data):
        """Validation croisée des filtres"""
        if data.get('date_from') and data.get('date_to'):
            if data['date_from'] > data['date_to']:
                raise serializers.ValidationError({
                    'date_to': 'La date de fin doit être postérieure à la date de début'
                })
        
        if data.get('amount_min') and data.get('amount_max'):
            if data['amount_min'] > data['amount_max']:
                raise serializers.ValidationError({
                    'amount_max': 'Le montant maximum doit être supérieur au montant minimum'
                })
        
        return data 