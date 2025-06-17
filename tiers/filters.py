import django_filters
from .models import Tiers
from django.db import models
"""
class TiersFilter(django_filters.FilterSet):
    flags = django_filters.CharFilter(method='filter_flags')

    class Meta:
        model = Tiers
        fields = ['type', 'flags']  # Ajoute d'autres champs si besoin

    def filter_flags(self, queryset, name, value):
        # Filtre les tiers dont le champ 'flags' contient la valeur recherchée
        return queryset.filter(**{f"{name}__contains": value})
    
    """
class TiersFilter(django_filters.FilterSet):
    # Filtre personnalisé pour le JSONField flags
    flags = django_filters.CharFilter(method='filter_flags')
    
    class Meta:
        model = Tiers
        fields = ['type', 'assigned_user', 'is_deleted']  # Champs normaux
        
        # Configuration pour gérer les JSONField automatiquement si besoin
        filter_overrides = {
            models.JSONField: {
                'filter_class': django_filters.CharFilter,
                'extra': lambda f: {
                    'lookup_expr': 'icontains',
                },
            },
        }
    
    def filter_flags(self, queryset, name, value):
        """
        Filtre personnalisé pour le champ flags (JSONField)
        Vous pouvez adapter cette méthode selon vos besoins
        """
        # Exemple : filtrer par clé dans le JSON
        # Si flags = {"active": true, "premium": false}
        # et value = "active", cela trouvera les tiers avec active: true
        
        try:
            # Si value est un JSON string
            import json
            json_value = json.loads(value)
            return queryset.filter(flags__contains=json_value)
        except (json.JSONDecodeError, ValueError):
            # Si value est une simple string, chercher dans les clés ou valeurs
            return queryset.filter(
                models.Q(flags__icontains=value) |
                models.Q(flags__contains={value: True}) |
                models.Q(flags__contains={value: False})
            )