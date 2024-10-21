"""Main routers by Pertro Flow project
presented for schemes:
:dct
:dcm
:sys
"""
from rest_framework import routers
from ..views.history import RecordHistoryAPIView


dcm_his_router = routers.DefaultRouter()

# routers for dictionaries
dcm_his_router.register(r'dcm/history', RecordHistoryAPIView)
