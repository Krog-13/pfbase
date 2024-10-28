"""Main routers by Pertro Flow project
presented for schemes:
:dct
:dcm
:sys
"""
from rest_framework import routers
from ..views.history import EHistoryAPIView


his_router = routers.DefaultRouter()
his_router.register(r"dct/history", EHistoryAPIView)
