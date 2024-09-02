from django.urls import path, include
from rest_framework import routers
from .views import DictionaryAPIView, DictIndicatorValueAPIView, DictIndicatorAPIView,\
    ElementAPIView, ElementListAPIView, GetVatView


router = routers.SimpleRouter()
router.register(r"dct/element", ElementAPIView)

urlpatterns = [
    # path("dict/element/", ElementAPIView.as_view()),

    path("dct/list/", DictionaryAPIView.as_view()),
    # path("dict/element/child/", ElementChildAPIView.as_view()), # use indicator from frontend
    path("dct/element/list/", ElementListAPIView.as_view()),
    path("dct/indicator/", DictIndicatorAPIView.as_view()),
    path("dct/values/", DictIndicatorValueAPIView.as_view(),
         name="reports-idc-values"),
    path('dct/vat/', GetVatView.as_view()),

    path("", include(router.urls))]
