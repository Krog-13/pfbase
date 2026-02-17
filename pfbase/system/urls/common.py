from django.urls import path
from ..views.common import FileAPIView, MailCheckAPI

common_urlpatterns = [
    path("stm/file/", FileAPIView.as_view()),
    path("stm/mail-check/", MailCheckAPI.as_view()),
    # path("stm/ecp/", EcpAPIView.as_view()),
]
