from django.conf import settings
from django.contrib.auth.models import Group, Permission
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.mail import send_mail
from django.db import IntegrityError, transaction
from django.urls import reverse
from django.utils import timezone
from django.shortcuts import render
from rest_framework import serializers, status
from rest_framework.generics import CreateAPIView, get_object_or_404
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import BasePermission, DjangoModelPermissions, IsAuthenticated, SAFE_METHODS
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from pfbase.pagination import CustomPagination
from ..models.user import User
from ..serializers.user import (UserSerializer, RegistrationUserSerializer, RolesSerializer,
    PermissionSerializer, ChangePasswordSerializer, SetPasswordSerializer,
    PasswordResetSerializer, PasswordResetConfirmSerializer)
from ..security import audit, create_reset, reset_password
from .security import PublicSecurityView, SecurityTokenObtainView, SessionLogoutView


class AccountModelPermissions(DjangoModelPermissions):
    perms_map = {**DjangoModelPermissions.perms_map,
                 'GET': ['%(app_label)s.view_%(model_name)s']}


class ManageAccountSecurity(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.has_perm('pfbase.manage_account_security')


class UserAPIView(ModelViewSet):
    queryset = User.objects.all().order_by('-id')
    serializer_class = UserSerializer
    permission_classes = (IsAuthenticated, AccountModelPermissions)
    pagination_class = CustomPagination

    def get_serializer_class(self):
        return RegistrationUserSerializer if self.action == 'create' else UserSerializer

    def perform_destroy(self, instance):
        if not self.request.user.has_perm('pfbase.manage_account_security'):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('Account security permission is required.')
        if instance.is_superuser and not self.request.user.is_superuser:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('Only a superuser may delete a superuser account.')
        instance.delete()


class RegistrationUserAPIView(CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegistrationUserSerializer
    permission_classes = (IsAuthenticated, AccountModelPermissions, ManageAccountSecurity)
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def create(self, request, *args, **kwargs):
        try:
            return super().create(request, *args, **kwargs)
        except IntegrityError:
            raise serializers.ValidationError('An account with these attributes already exists.')


class RoleManagementPermission(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and (request.method in SAFE_METHODS or request.user.is_superuser)


class RolesAPIView(ModelViewSet):
    queryset = Group.objects.all().order_by('id')
    serializer_class = RolesSerializer
    permission_classes = (IsAuthenticated, AccountModelPermissions, RoleManagementPermission)


class PermissionAPIView(ModelViewSet):
    queryset = Permission.objects.all().order_by('id')
    permission_classes = (IsAuthenticated, AccountModelPermissions, RoleManagementPermission)
    serializer_class = PermissionSerializer
    pagination_class = CustomPagination


# Legacy imports share the new lifecycle; no permanent authtoken can be issued.
CustomAuthToken = SecurityTokenObtainView
UserLogout = SessionLogoutView


class ChangePasswordViewSet(APIView):
    permission_classes = (IsAuthenticated,)

    def put(self, request):
        serializer = ChangePasswordSerializer(request.user, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(request.user)
        return Response({'message': 'Password changed; sign in again.'})


class SetPasswordViewSet(APIView):
    permission_classes = (IsAuthenticated, ManageAccountSecurity)

    def put(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        if user.is_superuser and not request.user.is_superuser:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('Only a superuser may reset a superuser password.')
        serializer = SetPasswordSerializer(user, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user)
        return Response({'message': 'Password set; previous sessions revoked.'})


class PasswordResetView(PublicSecurityView):
    def post(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # Same public response for missing, ambiguous, inactive and active accounts.
        with transaction.atomic():
            users = list(User.objects.select_for_update().filter(
                email__iexact=serializer.validated_data['email'], is_active=True).order_by('pk')[:2])
            if len(users) == 1:
                user = users[0]
                if user.expires_at is None or user.expires_at > timezone.now():
                    token = create_reset(user)
                    path = reverse('password-reset-confirm', kwargs={'uid': user.pk, 'token': token})
                    url = settings.PASSWORD_RESET_BASE_URL.rstrip('/') + path if settings.PASSWORD_RESET_BASE_URL else request.build_absolute_uri(path)
                    transaction.on_commit(lambda: send_mail('Password reset',
                        f'Use this one-time link to reset your password: {url}',
                        settings.DEFAULT_FROM_EMAIL, [user.email]))
        return Response({'message': 'If the account is eligible, a reset link has been sent.'})


class PasswordResetConfirmView(PublicSecurityView):
    parser_classes = (JSONParser, FormParser)

    def get(self, request, uid, token):
        response = render(request, 'resetForm.html', {'uid': uid, 'token': token})
        response['Referrer-Policy'] = 'no-referrer'
        return response

    def post(self, request, uid, token):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            reset_password(uid, token, serializer.validated_data['password'], request)
        except DjangoValidationError as error:
            raise serializers.ValidationError({'password': error.messages})
        return Response({'message': 'Password reset; sign in again.'})
