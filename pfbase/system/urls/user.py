"""Main routers by Pertro Flow project
presented for schemes:
:dct
:dcm
:sys
"""
from rest_framework import routers
from ..views.user import UserAPIView


user_router = routers.DefaultRouter()
user_router.register(r"stm/users", UserAPIView)
