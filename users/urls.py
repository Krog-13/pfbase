from django.urls import path, include
from rest_framework import routers
from .views import UserModelViewSet, RegisterUserApiView, OrganisationsAPIVIew, UserRolesModelViewSet, \
    UserSignModelViewSet, UserViewSet, UserPermissionAPIView, UserProfileViewSet, ConfirmEmailView

router = routers.SimpleRouter()
router.register(r"user/all", UserViewSet)

urlpatterns = [
    path("user/profile/", UserProfileViewSet.as_view({'get': 'retrieve', 'patch': 'update'})),


    path("users-list/", UserModelViewSet.as_view(), name="users-list"),
    path("user-roles/", UserRolesModelViewSet.as_view(), name="user-roles"),
    path("user-sign/", UserSignModelViewSet.as_view(), name="user-sign"),
    # path("user-current-sign/", UserSignCurrentModelViewSet.as_view(), name="user-current-sign"),
    
    path("register/", RegisterUserApiView.as_view(), name="register"),
    path('user/confirm/<uidb64>/<token>/', ConfirmEmailView.as_view(), name='confirm'),

    path("organizations-list/", OrganisationsAPIVIew.as_view(), name="organizations-list"),
    # path('send_email/', SendEmailView.as_view()),
    path('user/get-permission/', UserPermissionAPIView.as_view()),

    # path(r'^api/password_reset/', include('django_rest_passwordreset.urls', namespace='password_reset')),
    path("", include(router.urls)),
]
