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

    def get_queryset(self):
        """
        Return only the notifications belonging to the authenticated user.
        """
        user = self.request.user
        return Notification.objects.filter(receiver_user=user).order_by('-id')
