"""Main routers by Pertro Flow project
presented for schemes:
:dct
"""
from rest_framework import routers
from ..views.dictionaries import DictionariesAPIView

dct_router = routers.DefaultRouter()
dct_router.register(r"dct/dictionaries", DictionariesAPIView)
