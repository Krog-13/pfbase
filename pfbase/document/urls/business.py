from django.urls import path
from ..views.business import BusinessModelApiView, BusinessModelIndListApiView

business_router_urlpatterns = [
    path("dcm/business_router/<str:model_code>/", BusinessModelApiView.as_view()),
    path("dcm/business_router/<str:model_code>/<int:record_id>/", BusinessModelApiView.as_view()),
    path("dcm/check_indicators/<str:model_code>/", BusinessModelIndListApiView.as_view()),
]
