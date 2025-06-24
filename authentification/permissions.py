from rest_framework import permissions
from .models import Role, UserRole

class IsAdministrator(permissions.BasePermission):
    """
    Permission qui n'autorise que les utilisateurs avec le rôle 'Administrateur'
    """
    def has_permission(self, request, view):
        user = request.user
        if not user.is_authenticated:
            return False
        
        # Vérifier si l'utilisateur a le rôle 'Administrateur'
        admin_roles = UserRole.objects.filter(
            user=user,
            role__name='Administrateur'
        )
        
        return admin_roles.exists()

class IsAdminOrSuperUser(permissions.BasePermission):
    """
    Permission personnalisée pour restreindre l'accès aux administrateurs
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Vérifier si l'utilisateur est un superuser
        if request.user.is_superuser:
            return True
        
        # Vérifier si l'utilisateur a le rôle d'administrateur
        admin_role = Role.objects.filter(name='Administrateur').first()
        if admin_role:
            return UserRole.objects.filter(user=request.user, role=admin_role).exists()
        
        return False 