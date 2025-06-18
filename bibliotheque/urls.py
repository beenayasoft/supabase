from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CategorieViewSet, FournitureViewSet, MainOeuvreViewSet

router = DefaultRouter()
router.register(r'categories', CategorieViewSet)
router.register(r'fournitures', FournitureViewSet)
router.register(r'main-oeuvre', MainOeuvreViewSet)

urlpatterns = [
    path('', include(router.urls)),
] 