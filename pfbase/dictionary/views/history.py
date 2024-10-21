from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from pfbase.pagination import CustomPagination
from ..serializers.history import EHistorySerializer
from ..models.ehistory import ElementHistory


class EHistoryAPIView(ModelViewSet):
    """
    Представление истории
    """
    queryset = ElementHistory.objects.all().order_by('-id')
    serializer_class = EHistorySerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = CustomPagination

    @action(detail=False, methods=['get'], url_path='byelement/(?P<element_id>\d+)')
    def byelement(self, request, element_id=None):
        """
        Получения истории по :element_id
        """
        values = self.get_queryset().filter(element_id=element_id)
        if not values:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = self.serializer_class(values, many=True)
        return Response(serializer.data)
