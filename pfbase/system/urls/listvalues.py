"""Main routers by Pertro Flow project
presented for schemes:
:dct
:dcm
:sys
"""
from rest_framework import routers
from ..views.listvalues import LValuesAPIView


lv_router = routers.DefaultRouter()
lv_router.register(r"stm/list-values", LValuesAPIView)
