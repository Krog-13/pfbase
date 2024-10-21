"""Main routers by Pertro Flow project
presented for schemes:
:dct
:dcm
:sys
"""
from rest_framework import routers
from ..views.organization import OrganizationAPIView


org_router = routers.DefaultRouter()
org_router.register(r"stm/organization", OrganizationAPIView)
