"""
Main views by Pertro Flow project
presented for schemes:
:dct
"""
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from pfbase.base_views import AbstractModelAPIView
from pfbase.pagination import CustomPagination
from ..serializers.indicators import IndicatorSerializer
from ..models.indicators import DctIndicators


class IndicatorsAPIView(AbstractModelAPIView):
    """
    Представление :Indicator
    """
    queryset = DctIndicators.objects.all().order_by('-id')
    serializer_class = IndicatorSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = CustomPagination

    @action(detail=False, methods=['get'], url_path='bydictionary/(?P<pk>\w+)')
    def bydictionary(self, request, pk=None):
        """
        Получения индикаторов по :pk Dictionaries
        """
        if pk.isdigit():
            indicators = self.get_queryset().filter(dictionary_id=pk)
        else:
            indicators = self.get_queryset().filter(dictionary__code=pk)
        if not indicators:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = self.serializer_class(indicators, many=True, context={'request': request})
        return Response(serializer.data)
