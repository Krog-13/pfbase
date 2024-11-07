from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from pfbase.pagination import CustomPagination
from rest_framework.views import APIView
from ..serializers.user import UserSerializer, RegisterUserSerializer, GroupSerializer
from ..models.user import User
from django.contrib.auth.models import Group


class UserAPIView(ModelViewSet):
    """
    Представление пользователей
    """
    queryset = User.objects.all().order_by('-id')
    serializer_class = UserSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = CustomPagination


class RegisterUserAPIView(APIView):
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


class GroupAPIView(ModelViewSet):
    queryset = Group.objects.all().order_by('id')
    serializer_class = GroupSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = CustomPagination
