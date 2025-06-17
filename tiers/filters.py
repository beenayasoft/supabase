import django_filters
from .models import Tiers

class TiersFilter(django_filters.FilterSet):
    flags = django_filters.CharFilter(method='filter_flags')

    class Meta:
        model = Tiers
        fields = ['type', 'flags']  # Ajoute d'autres champs si besoin

    def filter_flags(self, queryset, name, value):
        # Filtre les tiers dont le champ 'flags' contient la valeur recherchée
        return queryset.filter(**{f"{name}__contains": value})
    
    