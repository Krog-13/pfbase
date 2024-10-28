"""Main routers by Pertro Flow project
presented for schemes:
:dct
:dcm
:sys
"""
from rest_framework import routers
from ..views.documents import DocumentsViewSet


dcm_router = routers.DefaultRouter()
dcm_router.register(r'dcm/documents', DocumentsViewSet)
