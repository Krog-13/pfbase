"""Main routers by Pertro Flow project
presented for schemes:
:dct
:dcm
:sys
"""
from rest_framework import routers
from ..views.rivalues import RIValueAPIView


riv_router = routers.DefaultRouter()
riv_router.register(r'dcm/values', RIValueAPIView)
