"""Main routers by Pertro Flow project
presented for schemes:
:dct
:dcm
:sys
"""
from rest_framework import routers
from django.urls import path
from ..views.user import UserAPIView, GroupAPIView, RegisterUserAPIView, PermissionAPIView
from ..views.user import CustomAuthToken, UserLogout

user_router = routers.DefaultRouter()
user_router.register(r"stm/users", UserAPIView)
user_router.register(r"stm/groups", GroupAPIView)
user_router.register(r"stm/permissions", PermissionAPIView)
user_urlpatterns = [
    path("stm/user/register/", RegisterUserAPIView.as_view()),
    path('api-token-auth/', CustomAuthToken.as_view()),
    path('api-token-logout/', UserLogout.as_view()),
]
