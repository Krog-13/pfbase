"""
Main routers by Pertro Flow project
presented for schemes:
:dct
:dcm
:sys
"""
from django.urls import path, include
from rest_framework import routers
from pfbase import views


router = routers.DefaultRouter()

# routers for dictionaries
router.register(r"dct/dictionaries", views.ABCDictionaryAPIView)
router.register(r"dct/indicators", views.DctIndicatorAPIView)
router.register(r"dct/elements", views.ElementAPIView)
router.register(r"dct/value", views.EIValueAPIView)
router.register(r"dct/history", views.ElementHistoryAPIView)

# routers for documents
router.register(r'dcm/documents', views.ABCDocumentViewSet)
router.register(r'dcm/indicators', views.DcmIndicatorAPIView)
router.register(r'dcm/records', views.RecordAPIView)
router.register(r'dcm/values', views.RIValueAPIView)
router.register(r'dcm/history', views.RecordHistoryAPIView)

# routers for system
router.register(r"sys/enum", views.PFEnumAPIView)
router.register(r"sys/notifications", views.NotificationAPIView)
router.register(r"sys/users", views.UserAPIView)

urlpatterns = [
    path("dct/element/", views.EIAPIView.as_view()),
    path("dct/element/<int:pk>/", views.EIAPIView.as_view()),

    path("dcm/record/", views.RIAPIView.as_view()),
    path("dcm/record/<int:pk>/", views.RIAPIView.as_view()),

    path("", include(router.urls))]
