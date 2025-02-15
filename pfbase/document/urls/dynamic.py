from django.urls import path
from ..views.dynamic import *

dynamic_router_urlpatterns = [
    path("dcm/dynamic_router/<str:model_code>/", DynamicApiView.as_view()),
    path("dcm/dynamic_router/<str:model_code>/<int:id>/", DynamicApiView.as_view()),
]
