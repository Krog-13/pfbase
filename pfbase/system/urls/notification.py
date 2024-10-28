"""Main routers by Pertro Flow project
presented for schemes:
:dct
:dcm
:sys
"""
from rest_framework import routers
from ..views.notification import NotificationAPIView


ntf_router = routers.DefaultRouter()
ntf_router.register(r"stm/notification", NotificationAPIView)
