from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import QuoteViewSet, QuoteItemViewSet

# Créer un routeur pour les ViewSets
router = DefaultRouter()
router.register(r'', QuoteViewSet)
router.register(r'quote-items', QuoteItemViewSet)

# Configuration des URLs
urlpatterns = [
    # URLs automatiques générées par le routeur DRF
    path('', include(router.urls)),
    
    # URLs personnalisées si nécessaire
    # path('quotes/export/<uuid:pk>/', QuoteExportView.as_view(), name='quote-export'),
    # path('quotes/pdf/<uuid:pk>/', QuotePDFView.as_view(), name='quote-pdf'),
]

# URLs disponibles:
# GET    /api/quotes/                     - Liste des devis avec filtres
# POST   /api/quotes/                     - Créer un nouveau devis
# GET    /api/quotes/{id}/                - Détail d'un devis
# PUT    /api/quotes/{id}/                - Modifier un devis complet
# PATCH  /api/quotes/{id}/                - Modifier partiellement un devis
# DELETE /api/quotes/{id}/                - Supprimer un devis
# GET    /api/quotes/stats/               - Statistiques globales
# POST   /api/quotes/{id}/mark_as_sent/   - Marquer comme envoyé
# POST   /api/quotes/{id}/mark_as_accepted/ - Marquer comme accepté
# POST   /api/quotes/{id}/mark_as_rejected/ - Marquer comme refusé
# POST   /api/quotes/{id}/mark_as_cancelled/ - Marquer comme annulé
# POST   /api/quotes/{id}/duplicate/      - Dupliquer un devis
# POST   /api/quotes/{id}/export/         - Exporter un devis

# GET    /api/quote-items/                - Liste des éléments de devis
# POST   /api/quote-items/                - Créer un nouvel élément
# GET    /api/quote-items/{id}/           - Détail d'un élément
# PUT    /api/quote-items/{id}/           - Modifier un élément complet
# PATCH  /api/quote-items/{id}/           - Modifier partiellement un élément
# DELETE /api/quote-items/{id}/           - Supprimer un élément
# GET    /api/quote-items/by_quote/       - Éléments d'un devis spécifique
# POST   /api/quote-items/reorder/        - Réorganiser les éléments
