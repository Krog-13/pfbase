from rest_framework.generics import get_object_or_404, ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet
from pfbase.pagination import CustomPagination
from ..serializers.notification import NotificationSerializer, NotificationShortSerializer
from ..models.notification import Notification
from rest_framework.decorators import action
from rest_framework.response import Response


class NotificationAPIView(ModelViewSet):
    """
    Представление уведомлений
    """
    queryset = Notification.objects.all().order_by('-id')
    serializer_class = NotificationSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = CustomPagination
    _default_count = 3

    def get_object(self):
        """
        Возвращает конкретное уведомление, проверяя, принадлежит ли оно текущему пользователю.
        """
        obj = get_object_or_404(Notification, id=self.kwargs["pk"])
        return obj

    def get_queryset(self, pk=None):
        """
        Return only the notifications belonging to the authenticated user.
        """
        user = self.request.user
        return Notification.objects.filter(receiver_user=user).order_by('-id')

    @action(detail=False, methods=['get'], url_path='short')
    def short(self, request):
        """
        Return short notification
        """
        count = request.query_params.get("count", self._default_count)
        notification = self.get_queryset().filter(receiver_user=request.user, is_read=False)[:int(count)]
        serializer = NotificationShortSerializer(notification, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='count')
    def count(self, request):
        """
        Return short notification
        """
        count_notification = self.get_queryset().filter(receiver_user=request.user, is_read=False).count()
        return Response({"count": count_notification})
