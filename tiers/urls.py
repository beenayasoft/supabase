from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TiersViewSet, AdresseViewSet, ContactViewSet, ActiviteTiersViewSet

router = DefaultRouter()
router.register(r'tiers', TiersViewSet, basename='tiers')
router.register(r'adresses', AdresseViewSet, basename='adresses')
router.register(r'contacts', ContactViewSet, basename='contacts')
router.register(r'activites', ActiviteTiersViewSet, basename='activites')

urlpatterns = [
    path('', include(router.urls)),
]