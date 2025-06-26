from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Router pour les ViewSets
router = DefaultRouter()
router.register(r'invoices', views.InvoiceViewSet, basename='invoice')
router.register(r'invoice-items', views.InvoiceItemViewSet, basename='invoiceitem')
router.register(r'payments', views.PaymentViewSet, basename='payment')

# URLs de l'app facturation
urlpatterns = [
    # API REST avec ViewSets
    path('api/', include(router.urls)),
]

# Structure des URLs générées par le router :
# 
# FACTURES (InvoiceViewSet):
# GET    /api/invoices/                     - Liste des factures avec filtres
# POST   /api/invoices/                     - Créer une nouvelle facture
# GET    /api/invoices/{id}/                - Détails d'une facture
# PUT    /api/invoices/{id}/                - Modifier une facture
# PATCH  /api/invoices/{id}/                - Modification partielle
# DELETE /api/invoices/{id}/                - Supprimer une facture
# 
# Actions personnalisées :
# POST   /api/invoices/from-quote/          - US 5.1: Créer depuis devis
# POST   /api/invoices/{id}/validate/       - US 5.3: Valider et émettre
# POST   /api/invoices/{id}/record-payment/ - US 5.4: Enregistrer règlement
# POST   /api/invoices/{id}/create-credit-note/ - US 5.5: Créer avoir
# GET    /api/invoices/stats/               - Statistiques de facturation
#
# ÉLÉMENTS DE FACTURE (InvoiceItemViewSet):
# GET    /api/invoice-items/                - Liste des éléments
# POST   /api/invoice-items/                - Créer un élément
# GET    /api/invoice-items/{id}/           - Détails d'un élément
# PUT    /api/invoice-items/{id}/           - Modifier un élément
# PATCH  /api/invoice-items/{id}/           - Modification partielle
# DELETE /api/invoice-items/{id}/           - Supprimer un élément
#
# PAIEMENTS (PaymentViewSet):
# GET    /api/payments/                     - Liste des paiements
# POST   /api/payments/                     - Créer un paiement
# GET    /api/payments/{id}/                - Détails d'un paiement
# PUT    /api/payments/{id}/                - Modifier un paiement
# PATCH  /api/payments/{id}/                - Modification partielle
# DELETE /api/payments/{id}/                - Supprimer un paiement 