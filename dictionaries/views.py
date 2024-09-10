from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from IEF.base_view import AbstractModelAPIView
from IEF.pagination import CustomPagination
from IEF.base_model import Enum
from .models import Indicator, ElementIndicatorValue, ABCDictionary, Element, ElementHistory
from .serializers import DictionarySerializer, IndicatorSerializer, \
    EIValueSerializer, ElementSerializer, ElementHistorySerializer, EnumSerializer


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
        indicators = Indicator.objects.filter(abc_dictionary_id=pk)
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

    @action(detail=False, methods=['get'], url_path='bydictionary/(?P<pk>\d+)')
    def bydictionary(self, request, pk=None):
        """
        Получения индикаторов по :pk ABCDictionary
        """
        indicators = self.get_queryset().filter(abc_dictionary_id=pk)
        if not indicators:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = IndicatorSerializer(indicators, many=True)
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


class EnumAPIView(AbstractModelAPIView):
    """
    Представление спарвочника :Enum (до 50 значений)
    """
    queryset = Enum.objects.all().order_by('id')
    serializer_class = EnumSerializer
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
        serializer = EnumSerializer(enums, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='bylistandcode/(?P<item>[^/.]+)/(?P<code>[^/.]+)')
    def bylistandcode(self, request, item=None, code=None):
        """
        Получения Enum по полям :list & code
        """
        enums = self.get_queryset().filter(list=item, code=code)
        if not enums:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = EnumSerializer(enums, many=True)
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
