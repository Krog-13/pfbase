from django.urls import path, include
from rest_framework import routers
from reports import views

# app_name = "api"
router = routers.DefaultRouter()
router.register(r'report-list1', views.GIndicatorAPIView)

urlpatterns = [
    path("rpt/category/", views.CategoryReportAPIView().as_view()),
    path("rpt/journal/", views.JournalReportAPIView().as_view()),
    path("rpt/journal/detail/", views.JournalDetailAPIView().as_view()),
    path("rpt/history/", views.JournalHistoryAPIView().as_view()),
    path("rpt/list/", views.ReportAPIView().as_view()),
    path("rpt/indicator/", views.ReportIndicatorAPIView.as_view()),
    path("rpt/values/", views.IndicatorValueAPIView().as_view()),

    path("", include(router.urls))
]
