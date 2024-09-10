from django.urls import path, include
from rest_framework import routers
from documents import views


router = routers.SimpleRouter()
router.register(r'dcm/documents', views.ABCDocumentViewSet)
router.register(r'dcm/indicators', views.IndicatorAPIView)
router.register(r'dcm/records', views.RecordAPIView)
router.register(r'dcm/values', views.RIValueAPIView)

router.register(r'dcm/history', views.RecordHistoryAPIView)

urlpatterns = [
    path("", include(router.urls)),
]
