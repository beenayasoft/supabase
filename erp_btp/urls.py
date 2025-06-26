"""
URL configuration for erp_btp project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    
    # API Authentication endpoints
    path("api/auth/", include("authentification.urls")),
    
    # API Bibliothèque d'ouvrages
    path("api/library/", include("bibliotheque.urls")),

    # API Tiers endpoints
    path("api/tiers/", include("tiers.urls")),
    
    # API Devis
    path("api/quotes/", include("devis.urls")),
    
    # API Facturation - Correction pour utiliser le préfixe /api/
    path("api/", include("facturation.urls")),
    
    # API Opportunités
    path("", include("opportunite.urls")),
    
    # API Documentation
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
]

# Ajout des URLs pour les médias en mode développement
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
