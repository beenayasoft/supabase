import django_filters
from django.db import models
from django.db.models import Q
from .models import Opportunity, OpportunityStatus, OpportunitySource, LossReason


class OpportunityFilter(django_filters.FilterSet):
    """Filtres pour les opportunités"""
    
    # Filtres principaux
    stage = django_filters.MultipleChoiceFilter(choices=OpportunityStatus.choices)
    source = django_filters.ChoiceFilter(choices=OpportunitySource.choices)
    loss_reason = django_filters.ChoiceFilter(choices=LossReason.choices)
    
    # Filtre de fourchettes
    min_amount = django_filters.NumberFilter(field_name='estimated_amount', lookup_expr='gte')
    max_amount = django_filters.NumberFilter(field_name='estimated_amount', lookup_expr='lte')
    min_probability = django_filters.NumberFilter(field_name='probability', lookup_expr='gte')
    max_probability = django_filters.NumberFilter(field_name='probability', lookup_expr='lte')
    
    # Filtres de dates
    created_after = django_filters.DateFilter(field_name='created_at', lookup_expr='gte')
    created_before = django_filters.DateFilter(field_name='created_at', lookup_expr='lte')
    closing_after = django_filters.DateFilter(field_name='expected_close_date', lookup_expr='gte')
    closing_before = django_filters.DateFilter(field_name='expected_close_date', lookup_expr='lte')
    
    # Filtres spécifiques pour le dashboard
    period = django_filters.CharFilter(method='filter_period')
    
    # Filtre de recherche global
    search = django_filters.CharFilter(method='filter_search')
    
    class Meta:
        model = Opportunity
        fields = ['stage', 'tier', 'source', 'assigned_to', 'loss_reason']
    
    def filter_search(self, queryset, name, value):
        """
        Recherche textuelle optimisée dans les champs pertinents
        """
        if not value:
            return queryset
            
        # Utiliser des requêtes distinctes pour chaque champ pour tirer parti des index
        name_results = set(queryset.filter(name__icontains=value).values_list('id', flat=True))
        assigned_results = set(queryset.filter(assigned_to__icontains=value).values_list('id', flat=True))
        
        # Ces requêtes peuvent être plus coûteuses car elles n'utilisent pas d'index directs
        # Nous les exécutons séparément pour ne pas ralentir les requêtes indexées
        description_results = set(queryset.filter(description__icontains=value).values_list('id', flat=True))
        tier_results = set(queryset.filter(tier__nom__icontains=value).values_list('id', flat=True))
        
        # Fusionner les résultats
        all_ids = name_results.union(assigned_results, description_results, tier_results)
        
        # Retourner le queryset filtré par les IDs trouvés
        return queryset.filter(id__in=all_ids)
        
    def filter_period(self, queryset, name, value):
        """
        Filtre par période (cette année, ce trimestre, ce mois, etc.)
        """
        from django.utils import timezone
        from datetime import timedelta
        
        if not value:
            return queryset
            
        today = timezone.now().date()
        
        if value == 'this_month':
            return queryset.filter(
                created_at__year=today.year,
                created_at__month=today.month
            )
        elif value == 'this_quarter':
            quarter_start_month = ((today.month - 1) // 3) * 3 + 1
            return queryset.filter(
                created_at__year=today.year,
                created_at__month__gte=quarter_start_month,
                created_at__month__lte=quarter_start_month + 2
            )
        elif value == 'this_year':
            return queryset.filter(created_at__year=today.year)
        elif value == 'last_30_days':
            return queryset.filter(
                created_at__gte=today - timedelta(days=30)
            )
        elif value == 'last_90_days':
            return queryset.filter(
                created_at__gte=today - timedelta(days=90)
            )
        
        return queryset 