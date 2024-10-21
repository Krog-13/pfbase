"""Main routers by Pertro Flow project
presented for schemes:
:dct
:dcm
:sys
"""
from rest_framework import routers
from ..views.indicators import IndicatorsAPIView

idc_router = routers.DefaultRouter()
idc_router.register(r"dct/indicators", IndicatorsAPIView)
