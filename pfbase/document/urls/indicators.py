"""Main routers by Pertro Flow project
presented for schemes:
:dct
:dcm
:sys
"""
from rest_framework import routers
from ..views.indicators import IndicatorsAPIView


dcm_idc_router = routers.DefaultRouter()

# routers for dictionaries
dcm_idc_router.register(r"dcm/indicators", IndicatorsAPIView)
