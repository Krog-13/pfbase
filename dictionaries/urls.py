from django.urls import path, include
from rest_framework import routers
from .views import DictionaryAPIView, CategoryDictionaryAPIView, DictIndicatorValueAPIView, DictIndicatorAPIView,\
    ElementAPIView, ElementChildAPIView, ElementListAPIView, GetVatView


router = routers.SimpleRouter()
router.register(r"dict/element", ElementAPIView)

urlpatterns = [
    # path("dict/element/", ElementAPIView.as_view()),

    path("dict/list/", DictionaryAPIView.as_view()),
    # path("dict/element/child/", ElementChildAPIView.as_view()), # use indicator from frontend
    path("dict/element/list/", ElementListAPIView.as_view()),
    path("dict/category/", CategoryDictionaryAPIView.as_view()),
    path("dict/indicator/", DictIndicatorAPIView.as_view()),
    path("dict/values/", DictIndicatorValueAPIView.as_view(),
         name="reports-idc-values"),
    path('dict/vat/', GetVatView.as_view()),

    path("", include(router.urls))]
