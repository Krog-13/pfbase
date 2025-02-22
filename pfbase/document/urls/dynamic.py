from django.urls import path
from ..views.business import BusinessApiView

dynamic_router_urlpatterns = [
    path("dcm/business_router/<str:model_code>/", BusinessApiView.as_view()),
    path("dcm/business_router/<str:model_code>/<int:record_id>/", BusinessApiView.as_view()),
]
