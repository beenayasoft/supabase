from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CategorieViewSet, FournitureViewSet, MainOeuvreViewSet,
    OuvrageViewSet, IngredientOuvrageViewSet
)

router = DefaultRouter()
router.register(r'categories', CategorieViewSet)
router.register(r'fournitures', FournitureViewSet)
router.register(r'main-oeuvre', MainOeuvreViewSet)
router.register(r'ouvrages', OuvrageViewSet)
router.register(r'ingredients', IngredientOuvrageViewSet)

urlpatterns = [
    path('', include(router.urls)),
] 