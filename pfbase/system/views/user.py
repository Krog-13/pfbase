from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet
from pfbase.pagination import CustomPagination
from ..serializers.user import UserSerializer
from ..models.user import User


class UserAPIView(ModelViewSet):
    """
    Представление пользователей
    """
    queryset = User.objects.all().order_by('-id')
    serializer_class = UserSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = CustomPagination
