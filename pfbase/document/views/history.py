"""
Main views by Pertro Flow project
presented for schemes:
:dct
:dcm
:sys
"""
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from pfbase.pagination import CustomPagination
from ..serializers.history import RHistorySerializer
from ..models.rhistory import RecordHistory


class RecordHistoryAPIView(ModelViewSet):
    """
    Представление истории
    """
    queryset = RecordHistory.objects.all().order_by('-id')
    serializer_class = RHistorySerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = CustomPagination

    @action(detail=False, methods=['get'], url_path='byrecord/(?P<record_id>\d+)')
    def byrecord(self, request, record_id=None):
        """
        Получения истории по :record_id
        """
        values = self.get_queryset().filter(record_id=record_id)
        if not values:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = self.serializer_class(values, many=True)
        return Response(serializer.data)
