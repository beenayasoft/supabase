from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import OpportunityViewSet

router = DefaultRouter()
router.register(r'opportunities', OpportunityViewSet, basename='opportunity')

urlpatterns = [
    path('api/', include(router.urls)),
]

# URLs disponibles :
# GET /api/opportunities/ - Liste des opportunités
# POST /api/opportunities/ - Créer une opportunité  
# GET /api/opportunities/{id}/ - Détail d'une opportunité
# PUT/PATCH /api/opportunities/{id}/ - Modifier une opportunité
# DELETE /api/opportunities/{id}/ - Supprimer une opportunité
# GET /api/opportunities/kanban/ - Vue Kanban
# GET /api/opportunities/stats/ - Statistiques
# PATCH /api/opportunities/{id}/update_stage/ - Mettre à jour le statut
# POST /api/opportunities/{id}/mark_won/ - Marquer comme gagnée
# POST /api/opportunities/{id}/mark_lost/ - Marquer comme perdue
# POST /api/opportunities/{id}/create_quote/ - Créer un devis
# GET /api/opportunities/{id}/timeline/ - Timeline de l'opportunité
