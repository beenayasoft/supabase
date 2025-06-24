from rest_framework import serializers
from .models import Devis, Lot, LigneDevis
from tiers.serializers import TiersDetailSerializer as TiersSerializer
from bibliotheque.serializers import OuvrageSerializer

class RoleBasedSerializerMixin:
    """
    Mixin pour filtrer les champs selon le rôle de l'utilisateur.
    """
    def __init__(self, *args, **kwargs):
        # Extraire le contexte de requête pour vérifier les permissions
        super().__init__(*args, **kwargs)
        request = self.context.get('request')
        
        # Filtrer les champs si l'utilisateur n'a pas le rôle approprié
        if request and not self.user_can_view_costs(request.user):
            cost_fields = ['debourse', 'total_debourse', 'marge', 'marge_totale', 'marge_globale']
            
            # Supprimer les champs liés aux coûts
            for field in cost_fields:
                if field in self.fields:
                    self.fields.pop(field)
    
    def user_can_view_costs(self, user):
        """
        Détermine si l'utilisateur peut voir les informations de coûts et marges.
        À remplacer par une implémentation réelle basée sur les rôles.
        """
        # Pour l'instant, tous les utilisateurs authentifiés peuvent voir les coûts
        # Dans une implémentation réelle, on vérifierait les rôles (gérant, admin)
        return user and user.is_authenticated if user else False

class LigneDevisSerializer(RoleBasedSerializerMixin, serializers.ModelSerializer):
    """
    Sérialiseur pour le modèle LigneDevis.
    """
    total_ht = serializers.DecimalField(read_only=True, max_digits=10, decimal_places=2)
    total_debourse = serializers.DecimalField(read_only=True, max_digits=10, decimal_places=2)
    marge = serializers.DecimalField(read_only=True, max_digits=5, decimal_places=2)
    
    class Meta:
        model = LigneDevis
        fields = [
            'id', 'lot', 'type', 'ouvrage', 'description', 'quantite', 
            'unite', 'prix_unitaire', 'debourse', 'ordre', 
            'total_ht', 'total_debourse', 'marge'
        ]

class LigneDevisCreateSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour la création d'une ligne de devis.
    """
    class Meta:
        model = LigneDevis
        fields = [
            'lot', 'type', 'ouvrage', 'description', 'quantite', 
            'unite', 'prix_unitaire', 'debourse', 'ordre'
        ]
    
    def validate(self, data):
        """
        Validation personnalisée pour les lignes de devis.
        """
        # Si le type est 'ouvrage', l'ouvrage est obligatoire
        if data.get('type') == 'ouvrage' and not data.get('ouvrage'):
            raise serializers.ValidationError(
                {"ouvrage": "L'ouvrage est obligatoire pour une ligne de type 'ouvrage'"}
            )
        
        # Si le type est 'manuel', ces champs sont obligatoires
        if data.get('type') == 'manuel':
            for field in ['description', 'unite', 'prix_unitaire', 'debourse']:
                if not data.get(field):
                    raise serializers.ValidationError(
                        {field: f"Le champ {field} est obligatoire pour une ligne de type 'manuel'"}
                    )
        
        return data

class LigneDevisDetailSerializer(RoleBasedSerializerMixin, serializers.ModelSerializer):
    """
    Sérialiseur détaillé pour le modèle LigneDevis.
    """
    ouvrage_details = OuvrageSerializer(source='ouvrage', read_only=True)
    total_ht = serializers.DecimalField(read_only=True, max_digits=10, decimal_places=2)
    total_debourse = serializers.DecimalField(read_only=True, max_digits=10, decimal_places=2)
    marge = serializers.DecimalField(read_only=True, max_digits=5, decimal_places=2)
    
    class Meta:
        model = LigneDevis
        fields = [
            'id', 'lot', 'type', 'ouvrage', 'ouvrage_details', 'description', 
            'quantite', 'unite', 'prix_unitaire', 'debourse', 'ordre', 
            'total_ht', 'total_debourse', 'marge'
        ]

class LotSerializer(RoleBasedSerializerMixin, serializers.ModelSerializer):
    """
    Sérialiseur pour le modèle Lot.
    """
    total_ht = serializers.DecimalField(read_only=True, max_digits=10, decimal_places=2)
    total_debourse = serializers.DecimalField(read_only=True, max_digits=10, decimal_places=2)
    marge = serializers.DecimalField(read_only=True, max_digits=5, decimal_places=2)
    
    class Meta:
        model = Lot
        fields = [
            'id', 'devis', 'nom', 'ordre', 'description', 
            'total_ht', 'total_debourse', 'marge'
        ]

class LotDetailSerializer(RoleBasedSerializerMixin, serializers.ModelSerializer):
    """
    Sérialiseur détaillé pour le modèle Lot, incluant ses lignes.
    """
    lignes = LigneDevisSerializer(many=True, read_only=True)
    total_ht = serializers.DecimalField(read_only=True, max_digits=10, decimal_places=2)
    total_debourse = serializers.DecimalField(read_only=True, max_digits=10, decimal_places=2)
    marge = serializers.DecimalField(read_only=True, max_digits=5, decimal_places=2)
    
    class Meta:
        model = Lot
        fields = [
            'id', 'devis', 'nom', 'ordre', 'description', 
            'lignes', 'total_ht', 'total_debourse', 'marge'
        ]

class DevisSerializer(RoleBasedSerializerMixin, serializers.ModelSerializer):
    """
    Sérialiseur pour le modèle Devis.
    """
    client_nom = serializers.SerializerMethodField()
    total_ht = serializers.DecimalField(read_only=True, max_digits=10, decimal_places=2)
    total_debourse = serializers.DecimalField(read_only=True, max_digits=10, decimal_places=2)
    marge_totale = serializers.DecimalField(read_only=True, max_digits=5, decimal_places=2)
    
    class Meta:
        model = Devis
        fields = [
            'id', 'client', 'client_nom', 'objet', 'statut', 'numero', 
            'date_creation', 'date_validite', 'commentaire', 'conditions_paiement', 
            'marge_globale', 'total_ht', 'total_debourse', 'marge_totale'
        ]
    
    def get_client_nom(self, obj):
        """
        Récupère le nom du client.
        """
        return obj.client.nom if obj.client else None

class DevisDetailSerializer(RoleBasedSerializerMixin, serializers.ModelSerializer):
    """
    Sérialiseur détaillé pour le modèle Devis, incluant ses lots et lignes.
    """
    client_details = TiersSerializer(source='client', read_only=True)
    lots = LotDetailSerializer(many=True, read_only=True)
    total_ht = serializers.DecimalField(read_only=True, max_digits=10, decimal_places=2)
    total_debourse = serializers.DecimalField(read_only=True, max_digits=10, decimal_places=2)
    marge_totale = serializers.DecimalField(read_only=True, max_digits=5, decimal_places=2)
    
    class Meta:
        model = Devis
        fields = [
            'id', 'client', 'client_details', 'objet', 'statut', 'numero', 
            'date_creation', 'date_validite', 'commentaire', 'conditions_paiement', 
            'marge_globale', 'lots', 'total_ht', 'total_debourse', 'marge_totale'
        ]

class DevisCreateSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour la création d'un devis.
    """
    class Meta:
        model = Devis
        fields = [
            'client', 'objet', 'statut', 'numero', 'date_validite', 
            'commentaire', 'conditions_paiement', 'marge_globale'
        ]
    
    def validate_numero(self, value):
        """
        Validation du numéro de devis.
        """
        # Vérifie que le numéro est unique
        if Devis.objects.filter(numero=value).exists():
            raise serializers.ValidationError("Ce numéro de devis existe déjà")
        return value 