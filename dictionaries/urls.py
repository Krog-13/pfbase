from django.urls import path, include
from rest_framework import routers
from dictionaries import views


router = routers.SimpleRouter()
router.register(r"dct/dictionaries", views.ABCDictionaryAPIView)
router.register(r"dct/indicators", views.IndicatorAPIView)
router.register(r"dct/elements", views.ElementAPIView)
router.register(r"dct/value", views.EIValueAPIView)

router.register(r"dct/history", views.ElementHistoryAPIView)
router.register(r"dct/enum", views.EnumAPIView)

urlpatterns = [
    path("", include(router.urls))]
