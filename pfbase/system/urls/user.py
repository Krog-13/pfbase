"""Main routers by Pertro Flow project
presented for schemes:
:dct
:dcm
:sys
"""
from rest_framework import routers
from django.urls import path
from ..views.user import (UserAPIView, RegistrationUserAPIView, PermissionAPIView, RolesAPIView,
                          CustomAuthToken, UserLogout, ChangePasswordViewSet, PasswordResetView,
                          PasswordResetConfirmView)

user_router = routers.DefaultRouter()
user_router.register(r"stm/users", UserAPIView)
user_router.register(r"stm/roles", RolesAPIView)
user_router.register(r"stm/permissions", PermissionAPIView)
user_urlpatterns = [
    path("stm/user/registration/", RegistrationUserAPIView.as_view()),
    path('api-token-auth/', CustomAuthToken.as_view()),
    path('api-token-logout/', UserLogout.as_view()),
    path('change-password/', ChangePasswordViewSet.as_view()),

    # password reset
    path('password-reset/', PasswordResetView.as_view(), name="password-reset"),
    path('password-reset-confirm/<int:uid>/<str:token>/', PasswordResetConfirmView.as_view(), name="password-reset-confirm"),
]
