"""Main routers by Pertro Flow project
presented for schemes:
:dct
:dcm
:sys
"""
from rest_framework import routers
from django.urls import path
from ..views.user import (
    UserAPIView,
    RegistrationUserAPIView,
    PermissionAPIView,
    RolesAPIView,
    ChangePasswordViewSet,
    PasswordResetView,
    PasswordResetConfirmView,
    SetPasswordViewSet
)
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
user_router = routers.DefaultRouter()
user_router.register(r"stm/users", UserAPIView)
user_router.register(r"stm/roles", RolesAPIView)
user_router.register(r"stm/permissions", PermissionAPIView)
user_urlpatterns = [
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),

    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    path('stm/user/registration/', RegistrationUserAPIView.as_view()),
    path('change-password/', ChangePasswordViewSet.as_view()),
    path('set-password/<int:pk>/', SetPasswordViewSet.as_view()),

    # password reset
    path('password-reset/', PasswordResetView.as_view(), name="password-reset"),
    path('password-reset-confirm/<int:uid>/<str:token>/', PasswordResetConfirmView.as_view(), name="password-reset-confirm"),
]
