from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import OpportunityViewSet

router = DefaultRouter()
router.register(r'opportunites', OpportunityViewSet, basename='opportunites')

urlpatterns = [
    path('', include(router.urls)),
    path('dashboard/commercial-summary/', OpportunityViewSet.as_view({'get': 'dashboard'}), name='commercial-summary'),
] 