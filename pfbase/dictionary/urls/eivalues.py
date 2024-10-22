"""Main routers by Pertro Flow project
presented for schemes:
:dct
"""
from rest_framework import routers
from ..views.eivalue import EIValuesAPIView


eiv_router = routers.DefaultRouter()
eiv_router.register(r"dct/values", EIValuesAPIView)
