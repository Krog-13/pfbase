from django.urls import path
from .views import DocsView

doc_urlpatterns = [
    path("docs/", DocsView.as_view()),
]
