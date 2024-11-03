"""
Main views by Pertro Flow project
presented for schemes:
:dct
:dcm
:sys
"""
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from pfbase.base_views import AbstractModelAPIView
from pfbase.pagination import CustomPagination
from ..serializers.indicators import IndicatorSerializer
from ..models.indicators import DcmIndicators


class IndicatorsAPIView(AbstractModelAPIView):
    """
    Представление :Indicator
    """
    queryset = DcmIndicators.objects.all().order_by('-id')
    serializer_class = IndicatorSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = CustomPagination

    @action(detail=False, methods=['get'], url_path='bydocument/(?P<pk>\d+)')
    def bydocument(self, request, pk=None):
        """
        Получения индикаторов по :pk Document
        """
        indicators = self.get_queryset().filter(document_id=pk)
        if not indicators:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = self.serializer_class(indicators, many=True, context={'request': request})
        return Response(serializer.data)
