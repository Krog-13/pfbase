from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from pfbase.pagination import CustomPagination
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from ..serializers.user import UserSerializer, RegisterUserSerializer, RolesSerializer, \
    PermissionSerializer, AuthTokenSerializer
from ..models.user import User
from rest_framework.views import APIView
from django.contrib.auth.models import Group
from rest_framework.generics import CreateAPIView
from django.contrib.auth.models import Permission


class UserAPIView(ModelViewSet):
    """
    Представление пользователей
    """
    queryset = User.objects.all().order_by('-id')
    serializer_class = UserSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = CustomPagination


class RegisterUserAPIView(CreateAPIView):
    """
    Регистрация нового пользователя
    """

    def post(self, request, *args, **kwargs):
        serializer = RegisterUserSerializer(data=request.data, context={'request': request})
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
        return Response({
            "token": token.key,
            "email": user.email,
            "user_id": user.pk,
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
