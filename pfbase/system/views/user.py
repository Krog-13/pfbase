from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.shortcuts import redirect
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet, ViewSet
from rest_framework.response import Response
from pfbase.pagination import CustomPagination
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from ..serializers.user import UserSerializer, RegistrationUserSerializer, RolesSerializer, \
    PermissionSerializer, AuthTokenSerializer, ChangePasswordSerializer, PasswordResetSerializer, \
    PasswordResetConfirmSerializer
from ..models.user import User
from rest_framework.views import APIView
from django.contrib.auth.models import Group
from django.urls import reverse
from django.core.mail import send_mail
from rest_framework.generics import CreateAPIView, get_object_or_404, UpdateAPIView
from django.contrib.auth.models import Permission
from ...permissions import IsOwnerOrReadOnly
from django.views.generic import TemplateView
from rest_framework.parsers import FormParser, JSONParser
from django.conf import settings


class UserAPIView(ModelViewSet):
    """
    Представление пользователей
    """
    queryset = User.objects.all().order_by('-id')
    serializer_class = UserSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = CustomPagination


class RegistrationUserAPIView(CreateAPIView):
    """
    Регистрация нового пользователя
    """

    def post(self, request, *args, **kwargs):
        serializer = RegistrationUserSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Пользователь успешно зарегистрирован"},
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RolesAPIView(ModelViewSet):
    queryset = Group.objects.all().order_by('id')
    serializer_class = RolesSerializer
    permission_classes = (IsAuthenticated,)


class PermissionAPIView(ModelViewSet):
    queryset = Permission.objects.all().order_by('id')
    permission_classes = (IsAuthenticated,)
    serializer_class = PermissionSerializer
    pagination_class = CustomPagination


class CustomAuthToken(ObtainAuthToken):
    """Customizing the ObtainAuthToken"""
    serializer_class = AuthTokenSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data,
                                           context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        token, created = Token.objects.get_or_create(user=user)
        roles = [gp.name for gp in user.groups.all()]
        fio = user.first_name +" "+ user.last_name
        return Response({
            "token": token.key,
            "email": user.email,
            "fio": fio,
            "user_id": user.pk,
            "organization": user.organization.code,
            "organization_name": user.organization.short_name, #Временно так сделал потом надо будет переделать
            "roles": roles,
        })


class UserLogout(APIView):
    permission_classes = (IsAuthenticated,)
    """Logout ObtainAuthToken"""
    def get(self, request, format=None):
        if request.user.is_anonymous:
            return Response({"message": "User not found"}, status=status.HTTP_400_BAD_REQUEST)
        request.user.auth_token.delete()
        return Response(status=status.HTTP_200_OK)


class ChangePasswordViewSet(UpdateAPIView):
    """Change password"""
    permission_classes = (IsAuthenticated, IsOwnerOrReadOnly)

    def put(self, request):
        obj = get_object_or_404(User, pk=request.user.id)
        serializer = ChangePasswordSerializer(obj, data=request.data)
        if serializer.is_valid():
            serializer.save(obj)
            obj.save()
            return Response({"message": "Пароль изменен успешно"}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetView(APIView):
    def post(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        if serializer.is_valid():
            user, token = serializer.save()
            reset_url = request.build_absolute_uri(
                reverse("password-reset-confirm", kwargs={"uid": user.id, "token": token})
            )
            user.email_user("Password Reset Request", f"Click the link to reset your password: {reset_url}",
                            settings.EMAIL_HOST_USER)
            return Response({"message": "Password reset link sent"}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetConfirmView(APIView, TemplateView):
    parser_classes = [FormParser, JSONParser]
    template_name = 'reset.html'

    def post(self, request, uid, token):
        try:
            user = User.objects.get(pk=uid)
            token_generator = PasswordResetTokenGenerator()
            if not token_generator.check_token(user, token):
                return Response({"error": "Invalid or expired token."}, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            return Response({"error": "Invalid user."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = PasswordResetConfirmSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user)
            return redirect("/login")
            return Response({"message": "Password reset successful."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
