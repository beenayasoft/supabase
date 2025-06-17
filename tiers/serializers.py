from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Tiers, Adresse, Contact, ActiviteTiers

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    """Serializer pour les informations utilisateur dans les relations"""
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name']


class AdresseSerializer(serializers.ModelSerializer):
    """Serializer pour les adresses"""
    class Meta:
        model = Adresse
        fields = [
            'id', 'libelle', 'rue', 'ville', 'code_postal', 'pays', 
            'facturation', 'date_creation', 'date_modification'
        ]
        read_only_fields = ['id', 'date_creation', 'date_modification']


class ContactSerializer(serializers.ModelSerializer):
    """Serializer pour les contacts"""
    class Meta:
        model = Contact
        fields = [
            'id', 'nom', 'prenom', 'fonction', 'email', 'telephone',
            'contact_principal_devis', 'contact_principal_facture',
            'date_creation', 'date_modification'
        ]
        read_only_fields = ['id', 'date_creation', 'date_modification']


class ActiviteTiersSerializer(serializers.ModelSerializer):
    """Serializer pour les activités"""
    utilisateur = UserSerializer(read_only=True)
    
    class Meta:
        model = ActiviteTiers
        fields = ['id', 'type', 'utilisateur', 'contenu', 'date']
        read_only_fields = ['id', 'utilisateur', 'date']


class TiersListSerializer(serializers.ModelSerializer):
    """Serializer pour la liste des tiers (version allégée)"""
    assigned_user = UserSerializer(read_only=True)
    ville_principale = serializers.SerializerMethodField()
    date_derniere_activite = serializers.SerializerMethodField()
    
    class Meta:
        model = Tiers
        fields = [
            'id', 'nom', 'type', 'flags', 'assigned_user', 
            'ville_principale', 'date_derniere_activite', 'date_creation'
        ]
    
    def get_ville_principale(self, obj):
        """Récupérer la ville de l'adresse principale"""
        adresse_facturation = obj.adresses.filter(facturation=True).first()
        if adresse_facturation:
            return adresse_facturation.ville
        adresse_principale = obj.adresses.first()
        return adresse_principale.ville if adresse_principale else None
    
    def get_date_derniere_activite(self, obj):
        """Récupérer la date de la dernière activité"""
        derniere_activite = obj.activites.first()
        return derniere_activite.date if derniere_activite else None


class TiersDetailSerializer(serializers.ModelSerializer):
    """Serializer pour le détail complet d'un tier (vue 360°)"""
    assigned_user = UserSerializer(read_only=True)
    adresses = AdresseSerializer(many=True, read_only=True)
    contacts = ContactSerializer(many=True, read_only=True)
    activites = ActiviteTiersSerializer(many=True, read_only=True)
    
    class Meta:
        model = Tiers
        fields = [
            'id', 'type', 'nom', 'siret', 'tva', 'flags', 'assigned_user',
            'date_creation', 'date_modification', 'date_archivage',
            'adresses', 'contacts', 'activites'
        ]
        read_only_fields = ['id', 'date_creation', 'date_modification', 'date_archivage']


class TiersCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer pour la création et modification des tiers"""
    adresses = AdresseSerializer(many=True, required=False)
    contacts = ContactSerializer(many=True, required=False)
    
    class Meta:
        model = Tiers
        fields = [
            'type', 'nom', 'siret', 'tva', 'flags', 'assigned_user',
            'adresses', 'contacts'
        ]
    
    def create(self, validated_data):
        """Créer un tier avec ses adresses et contacts"""
        adresses_data = validated_data.pop('adresses', [])
        contacts_data = validated_data.pop('contacts', [])
        
        # Créer le tier
        tier = Tiers.objects.create(**validated_data)
        
        # Créer les adresses
        for adresse_data in adresses_data:
            Adresse.objects.create(tier=tier, **adresse_data)
        
        # Créer les contacts
        for contact_data in contacts_data:
            Contact.objects.create(tier=tier, **contact_data)
        
        # Créer une activité de création
        ActiviteTiers.objects.create(
            tier=tier,
            type=ActiviteTiers.TYPE_CREATION,
            utilisateur=self.context['request'].user,
            contenu="Fiche tier créée"
        )
        
        return tier
    
    def update(self, instance, validated_data):
        """Mettre à jour un tier avec ses adresses et contacts"""
        adresses_data = validated_data.pop('adresses', [])
        contacts_data = validated_data.pop('contacts', [])
        
        # Mettre à jour le tier
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Gérer les adresses (remplacer complètement)
        instance.adresses.all().delete()
        for adresse_data in adresses_data:
            Adresse.objects.create(tier=instance, **adresse_data)
        
        # Gérer les contacts (remplacer complètement)
        instance.contacts.all().delete()
        for contact_data in contacts_data:
            Contact.objects.create(tier=instance, **contact_data)
        
        # Créer une activité de modification
        ActiviteTiers.objects.create(
            tier=instance,
            type=ActiviteTiers.TYPE_MODIFICATION,
            utilisateur=self.context['request'].user,
            contenu="Fiche tier modifiée"
        )
        
        return instance


class ActiviteTiersCreateSerializer(serializers.ModelSerializer):
    """Serializer pour créer une nouvelle activité"""
    class Meta:
        model = ActiviteTiers
        fields = ['type', 'contenu']
    
    def create(self, validated_data):
        """Créer une activité avec l'utilisateur connecté"""
        validated_data['utilisateur'] = self.context['request'].user
        validated_data['tier'] = self.context['tier']
        return super().create(validated_data)