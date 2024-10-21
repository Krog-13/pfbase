from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet
from pfbase.pagination import CustomPagination
from ..serializers.notification import NotificationSerializer
from ..models.notification import Notification


class NotificationAPIView(ModelViewSet):
    """
    Представление уведомлений
    """
    queryset = Notification.objects.all().order_by('-id')
    serializer_class = NotificationSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = CustomPagination
