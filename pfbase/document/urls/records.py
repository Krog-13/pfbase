"""Main routers by Pertro Flow project
presented for schemes:
:dcm
"""
from rest_framework import routers
from django.urls import path
from ..views.records import RecordAPIView, RIAPIView


rct_router = routers.DefaultRouter()
rct_router.register(r'dcm/records', RecordAPIView)

rct_urlpatterns = [
    path("dcm/record/", RIAPIView.as_view()),
    path("dcm/record/<int:pk>/", RIAPIView.as_view()),
    path("dcm/records/indicator/", RIAPIView.as_view())
]
