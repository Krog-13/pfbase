"""
Main views by Pertro Flow project
presented for schemes:
:dct
:dcm
:sys
"""
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from .base_views import AbstractModelAPIView
from .pagination import CustomPagination
from .models import DctIndicator, ElementIndicatorValue, ABCDictionary, Element, ElementHistory, \
    ABCDocument, DcmIndicator, Record, RecordIndicatorValue, RecordHistory, PFEnum
from .serializers import DictionarySerializer, DctIndicatorSerializer, \
    EIValueSerializer, ElementSerializer, ElementHistorySerializer, PFEnumSerializer, \
    ABCDocumentSerializer, DcmIndicatorSerializer, RIValueSerializer, RecordSerializer, RecordHistorySerializer


# Views for Dictionary
class ABCDictionaryAPIView(AbstractModelAPIView):
    """
    Представление :ABCDictionary
    """
    queryset = ABCDictionary.objects.all().order_by('id')
    serializer_class = DictionarySerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = CustomPagination

    @action(detail=True, methods=['get'])
    def indicator(self, request, pk=None):
        """
        Получения индикторов по :pk ABCDictionary
        """
        indicators = DctIndicator.objects.filter(abc_dictionary_id=pk)
        if not indicators:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = DctIndicatorSerializer(indicators, many=True)
        return Response(serializer.data)


class DctIndicatorAPIView(AbstractModelAPIView):
    """
    Представление :Indicator
    """
    queryset = DctIndicator.objects.all().order_by('id')
    serializer_class = DctIndicatorSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = CustomPagination

    @action(detail=False, methods=['get'], url_path='bydictionary/(?P<pk>\d+)')
    def bydictionary(self, request, pk=None):
        """
        Получения индикаторов по :pk ABCDictionary
        """
        indicators = self.get_queryset().filter(abc_dictionary_id=pk)
        if not indicators:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = DctIndicatorSerializer(indicators, many=True)
        return Response(serializer.data)


class ElementAPIView(AbstractModelAPIView):
    """
    Представление :Element
    """
    queryset = Element.objects.all()
    serializer_class = ElementSerializer
    permission_classes = (IsAuthenticated,)

    @action(detail=False, methods=['get'], url_path='bydictionary/(?P<pk>\d+)')
    def bydictionary(self, request, pk=None):
        """
        Получения элементов по :pk ABCDictionary
        """
        indicators = self.get_queryset().filter(abc_dictionary_id=pk)
        if not indicators:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = ElementSerializer(indicators, many=True)
        return Response(serializer.data)


class EIValueAPIView(ModelViewSet):
    """
    Предтавление значения по :индикатору и :элементу
    """
    queryset = ElementIndicatorValue.objects.all().order_by('id')
    serializer_class = EIValueSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = CustomPagination

    @action(detail=False, methods=['get'], url_path='byelement/(?P<element_id>\d+)')
    def byelement(self, request, element_id=None):
        """
        Получения значений по :element_id
        """
        values = self.get_queryset().filter(element_id=element_id)
        if not values:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = EIValueSerializer(values, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='byindicator/(?P<indicator_id>\d+)')
    def byindicator(self, request, indicator_id=None):
        """
        Получения значений по :indicator_id
        """
        values = self.get_queryset().filter(indicator_id=indicator_id)
        if not values:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = EIValueSerializer(values, many=True)
        return Response(serializer.data)


class ElementHistoryAPIView(ModelViewSet):
    """
    Представление истории
    """
    queryset = ElementHistory.objects.all().order_by('id')
    serializer_class = ElementHistorySerializer
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
        serializer = ElementHistorySerializer(values, many=True)
        return Response(serializer.data)


# Views for Documents
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
        indicators = DcmIndicator.objects.filter(abc_document_id=pk)
        if not indicators:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = DcmIndicatorSerializer(indicators, many=True)
        return Response(serializer.data)


class DcmIndicatorAPIView(AbstractModelAPIView):
    """
    Представление :Indicator
    """
    queryset = DcmIndicator.objects.all().order_by('id')
    serializer_class = DcmIndicatorSerializer
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
        serializer = DcmIndicatorSerializer(indicators, many=True)
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


# Views for System
class PFEnumAPIView(AbstractModelAPIView):
    """
    Представление спарвочника :Enum (до 50 значений)
    """
    queryset = PFEnum.objects.all().order_by('id')
    serializer_class = PFEnumSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = CustomPagination

    @action(detail=False, methods=['get'], url_path='bylist/(?P<item>[^/.]+)')
    def bylist(self, request, item=None):
        """
        Получения Enum по полю :list
        """
        enums = self.get_queryset().filter(list=item)
        if not enums:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = PFEnumSerializer(enums, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='bylistandcode/(?P<item>[^/.]+)/(?P<code>[^/.]+)')
    def bylistandcode(self, request, item=None, code=None):
        """
        Получения Enum по полям :list & code
        """
        enums = self.get_queryset().filter(list=item, code=code)
        if not enums:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = PFEnumSerializer(enums, many=True)
        return Response(serializer.data)
