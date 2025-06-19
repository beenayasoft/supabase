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
    # Nouveau filtre pour le champ relation
    relation = django_filters.ChoiceFilter(choices=Tiers.RELATION_CHOICES)
    
    # Filtre personnalisé pour le JSONField flags (compatibilité)
    flags = django_filters.CharFilter(method='filter_flags')
    
    # Filtre de recherche global
    search = django_filters.CharFilter(method='filter_search')
    
    class Meta:
        model = Tiers
        fields = ['type', 'relation', 'assigned_user', 'is_deleted']
        
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
        Filtre personnalisé pour le champ flags (JSONField) - DEPRECATED
        Maintenu pour compatibilité pendant la transition
        """
        # Pendant la migration, on peut aussi filtrer par relation si flags correspond
        if value in ['client', 'prospect', 'fournisseur', 'sous_traitant']:
            # Utiliser le nouveau champ relation si disponible
            relation_queryset = queryset.filter(relation=value)
            if relation_queryset.exists():
                return relation_queryset
        
        # Fallback vers l'ancien système flags
        try:
            import json
            json_value = json.loads(value)
            return queryset.filter(flags__contains=json_value)
        except (json.JSONDecodeError, ValueError):
            return queryset.filter(
                models.Q(flags__icontains=value) |
                models.Q(flags__contains=[value])
            )
    
    def filter_search(self, queryset, name, value):
        """
        Filtre de recherche global sur nom, siret, et informations de contact
        """
        return queryset.filter(
            models.Q(nom__icontains=value) |
            models.Q(siret__icontains=value) |
            models.Q(contacts__nom__icontains=value) |
            models.Q(contacts__prenom__icontains=value) |
            models.Q(contacts__email__icontains=value)
        ).distinct()