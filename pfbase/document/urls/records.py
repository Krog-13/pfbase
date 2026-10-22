"""Main routers by Pertro Flow project
presented for schemes:
:dcm
"""
from rest_framework import routers
from django.urls import path
from ..views.records import RecordAPIView, RIAPIView, RIPLAPIView, TestApiView


rct_router = routers.DefaultRouter()
rct_router.register(r'dcm/records/all', RecordAPIView)

rct_urlpatterns = [
    path("dcm/records/", RIAPIView.as_view()),
    path("dcm/records/<int:pk>/restore/", RIAPIView.as_view()),
    path("dcm/records/<int:pk>/", RIAPIView.as_view()),

    path("dcm/records/list/", RIPLAPIView.as_view(), name="records-list"),
    path("dcm/records/pack/", RIPLAPIView.as_view(), name="records-pack"),

    path("dcm/test/", TestApiView.as_view()),
]
