from django.urls import path
from ..views.common import FileAPIView

common_urlpatterns = [
    path("stm/file/", FileAPIView.as_view()),
    # path("stm/ecp/", EcpAPIView.as_view()),
]
