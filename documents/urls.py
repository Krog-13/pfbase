from django.urls import path, include
from rest_framework import routers
from documents import views
from .models import CategoryDocument, FieldValue, JournalDocument
from .views import JournalViewSet


router = routers.SimpleRouter()
# router.register(r'doc/journal', JournalModeViewSet)

urlpatterns = [
    path("doc/journal/", JournalViewSet.as_view({'get': 'list', 'patch': 'update', 'create': 'post'})),
    path("doc/journal/indicator/", views.DocumentFieldAPIView.as_view()),
    path("doc/journal/values/", views.DocumentValueAPIView.as_view()),
    path("doc/journal/vacancy/", views.DocumentVacancyAPIView.as_view()),
    path("doc/journal/file/", views.DocumentFileAPIView.as_view()),

    # path("doc/journal/detail/", views.JournalDetailAPIView.as_view()),
    # path("doc/category/", views.CategoryDocumentAPIView().as_view(), name="doc-cat-list"),
    path("doc/journalDev/<int:pk>/", views.JournalAPIView.as_view()),
    path("doc/journalSet/<int:pk>/", views.JournalModeViewSet2.as_view({"get": "list"})),
    # path("doc/journalSet/<int:pk>/", views.JournalModeViewSet.as_view({"get": "list"})),
    path("doc/journalRet/<int:pk>/", views.JournalUpdateAPIView().as_view()),
    path("doc/journalUpdate/<int:pk>/", views.JournalUpdate2APIView().as_view()),
    # path("doc/journalList/", views.JournalListAPIView.as_view(queryset=JournalDocument.objects.all())), # можно передать как аргумент
    path("doc/journalList/", views.JournalListAPIView.as_view()),
    # path("doc/journal/", views.JournalDocumentAPIView().as_view()),
    # path("doc/journal/<int:pk>/", views.JournalDocumentUpdateAPIView().as_view()),

    # path("doc/journal/update/", views.JournalDocumentUpdateAPIView().as_view()),
    # path("doc/journal/file/", views.JournalDocumentFileAPIView().as_view()),
    path("doc/journal/value/", views.JournalValueAPIView().as_view()),
    path("doc/history/", views.JournalHistoryAPIView().as_view()),
    path("doc/list/", views.DocumentAPIView().as_view(), name="doc-list"),
    # path("doc/indicator/", views.DocumentFieldAPIView.as_view(), name="doc-idc-list"),
    path("doc/values/", views.FieldValueAPIViewOLD().as_view(), name="documents-fld-values"),
    path('get-notification/', views.GetNotificationView.as_view()),
    path("docs/", views.DocumentationAPIVIew.as_view(), name="documentation"),
    path("", include(router.urls)),
]
