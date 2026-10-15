"""
URL configuration for PFBase core.
Include:
- Grappelli admin interface
- Django admin documentation
- Django admin site
- API token authentication
- API schema generation
- Swagger UI for API documentation
- Redoc for API documentation
"""

from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import path, include
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

urlpatterns = [
    path('grappelli/', include('grappelli.urls')),
    path('admin/doc/', include('django.contrib.admindocs.urls')),
    path('admin/', admin.site.urls),
    path('api/', include('pfbase.urls')),
]

urlpatterns += staticfiles_urlpatterns()
