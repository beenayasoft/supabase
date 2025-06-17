from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _

class User(AbstractUser):
    """
    Modèle utilisateur personnalisé avec email comme identifiant principal
    et champ entreprise supplémentaire
    """
    email = models.EmailField(_('email address'), unique=True)
    company = models.CharField(max_length=255, blank=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    def __str__(self):
        return self.email
