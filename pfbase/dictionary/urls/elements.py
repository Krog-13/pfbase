"""Main routers by Pertro Flow project
presented for schemes:
:dct
"""
from rest_framework import routers
from django.urls import path, include
from ..views.elements import ElementsAPIView, EIAPIView, FileUploadView, FileUploadElementsView


elm_router = routers.DefaultRouter()
elm_router.register(r"dct/elements", ElementsAPIView)

elm_urlpatterns = [
    path("dct/element/", EIAPIView.as_view()),
    path("dct/element/<int:pk>/", EIAPIView.as_view()),
    path("dct/element/<str:code>/", EIAPIView.as_view()),

    path("dct/element/export/file/", FileUploadView.as_view()),
    path("dct/element/export/file/v2/", FileUploadElementsView.as_view()),
    path("", include(elm_router.urls)),
]
