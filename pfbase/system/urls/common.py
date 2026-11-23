from django.urls import path
from ..views.common import FileAPIView, MailCheckAPI, AccountUpload

common_urlpatterns = [
    path("stm/file/", FileAPIView.as_view()),
    path("stm/upload-account/", AccountUpload.as_view()),
    path("stm/mail-check/", MailCheckAPI.as_view()),
    # path("stm/ecp/", EcpAPIView.as_view()),
]
