from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from IEF.base_view import AbstractModelAPIView
from IEF.pagination import CustomPagination
from .models import Record, ABCDocument, RecordHistory, Indicator, RecordIndicatorValue
from .serializers import RecordSerializer, \
    ABCDocumentSerializer, IndicatorSerializer, RIValueSerializer, RecordHistorySerializer


class ABCDocumentViewSet(AbstractModelAPIView):
    """
    Представление :ABCDocument
    """
    queryset = ABCDocument.objects.all()
    serializer_class = ABCDocumentSerializer
    permission_classes = (IsAuthenticated,)

    @action(detail=True, methods=['get'])
    def indicator(self, request, pk=None):
        """
        Получения индикторов по :pk ABCDocument
        """
        indicators = Indicator.objects.filter(abc_document_id=pk)
        if not indicators:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = IndicatorSerializer(indicators, many=True)
        return Response(serializer.data)


class IndicatorAPIView(AbstractModelAPIView):
    """
    Представление :Indicator
    """
    queryset = Indicator.objects.all().order_by('id')
    serializer_class = IndicatorSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = CustomPagination

    @action(detail=False, methods=['get'], url_path='bydocument/(?P<pk>\d+)')
    def bydocument(self, request, pk=None):
        """
        Получения индикаторов по :pk ABCDocument
        """
        indicators = self.get_queryset().filter(abc_document_id=pk)
        if not indicators:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = IndicatorSerializer(indicators, many=True)
        return Response(serializer.data)


class RecordAPIView(ModelViewSet):
    """
    Представление :Record
    """
    queryset = Record.objects.all().order_by('id')
    serializer_class = RecordSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = CustomPagination

    @action(detail=False, methods=['get'], url_path='bydocument/(?P<pk>\d+)')
    def bydocument(self, request, pk=None):
        """
        Получения записей по :pk ABCDocument
        """
        indicators = self.get_queryset().filter(abc_document_id=pk)
        if not indicators:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = RecordSerializer(indicators, many=True)
        return Response(serializer.data)


class RIValueAPIView(ModelViewSet):
    """
    Предтавление значения по :индикатору и :записи
    """
    queryset = RecordIndicatorValue.objects.all().order_by('id')
    serializer_class = RIValueSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = CustomPagination

    @action(detail=False, methods=['get'], url_path='byrecord/(?P<record_id>\d+)')
    def byrecord(self, request, record_id=None):
        """
        Получения значений по :record_id
        """
        values = self.get_queryset().filter(record_id=record_id)
        if not values:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = RIValueSerializer(values, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='byindicator/(?P<indicator_id>\d+)')
    def byindicator(self, request, indicator_id=None):
        """
        Получения значений по :indicator_id
        """
        values = self.get_queryset().filter(indicator_id=indicator_id)
        if not values:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = RIValueSerializer(values, many=True)
        return Response(serializer.data)


class RecordHistoryAPIView(ModelViewSet):
    """
    Представление истории
    """
    queryset = RecordHistory.objects.all().order_by('id')
    serializer_class = RecordHistorySerializer
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
        serializer = RecordHistorySerializer(values, many=True)
        return Response(serializer.data)
