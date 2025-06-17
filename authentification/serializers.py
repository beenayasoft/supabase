from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    """
    Serializer pour afficher les informations de l'utilisateur
    """
    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'first_name', 'last_name', 'company']
        read_only_fields = ['id']

class RegisterSerializer(serializers.ModelSerializer):
    """
    Serializer pour l'inscription d'un nouvel utilisateur
    """
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ['email', 'username', 'password', 'password2', 'first_name', 'last_name', 'company']

    def validate(self, attrs):
        """
        Valide que les deux mots de passe correspondent
        """
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Les mots de passe ne correspondent pas."})
        return attrs

    def create(self, validated_data):
        """
        Crée un nouvel utilisateur avec les données validées
        """
        # Supprimer le champ password2 qui n'est pas dans le modèle
        validated_data.pop('password2')
        
        # Créer l'utilisateur
        user = User.objects.create_user(**validated_data)
        return user 