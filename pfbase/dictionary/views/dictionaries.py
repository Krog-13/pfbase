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
from ..serializers import dictionaries, indicators
from ..models.dictionaries import Dictionaries
from ..models.indicators import DctIndicators


# Views for Dictionary
class DictionariesAPIView(AbstractModelAPIView):
    """
    Представление :Dictionaries
    """
    queryset = Dictionaries.objects.all().order_by('-id')
    serializer_class = dictionaries.DictionarySerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = CustomPagination

    @action(detail=True, methods=['get'])
    def indicator(self, request, pk=None):
        """
        Получения индикторов по :pk Dictionaries
        """
        dct_indicators = DctIndicators.objects.filter(dictionary_id=pk)
        if not dct_indicators:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = indicators.IndicatorSerializer(dct_indicators, many=True, context={'request': request})
        return Response(serializer.data)
