from rest_framework import status, views, exceptions as exc
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from pfbase.base_views import AbstractModelAPIView
from pfbase.pagination import CustomPagination
from pfbase.exception import WrongType
from django.db import IntegrityError
from pfbase import service
from ..serializers.elements import EIGetSerializer, EIPostSerializer, EIUpdateSerializer, ElementSerializer
from ..models import elements, dictionaries, indicators, ElementIndicatorValues


class ElementsAPIView(AbstractModelAPIView):
    """
    Представление :Element
    """
    queryset = elements.Elements.objects.all().order_by('-id')
    serializer_class = EIGetSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = CustomPagination

    @action(detail=False, methods=['get'], url_path='bydictionary/(?P<pk>\d+)')
    def bydictionary(self, request, pk=None):
        """
        Получения элементов по :pk ABCDictionary
        """
        indicators = self.get_queryset().filter(abc_dictionary_id=pk)
        if not indicators:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = EIGetSerializer(indicators, many=True)
        return Response(serializer.data)


class EIAPIView(views.APIView):
    """
    Представление :Element with their :Indicator
    """
    queryset = elements.Elements.objects.all()
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        pk = kwargs.get('pk', False)
        if not pk:
            return Response({"message": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        try:
            queryset = self.queryset.get(id=pk)
        except elements.Elements.DoesNotExist:
            return Response({"message": "Element not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response(EIGetSerializer(queryset, many=False).data)

    def post(self, request):
        serializer = EIPostSerializer(data=request.data)
        if serializer.is_valid():
            try:
                output = service.create_element_row(self.request.user, serializer.validated_data)
            except (dictionaries.Dictionaries.DoesNotExist, indicators.DctIndicators.DoesNotExist):
                return Response({"message": "Неверный code|id|type абстракции"},
                                         status=status.HTTP_400_BAD_REQUEST)
            except elements.Elements.DoesNotExist:
                return Response({"message": "Неверный parent_id элемента"},
                                         status=status.HTTP_400_BAD_REQUEST)
            except WrongType:
                return Response({"message": "Неверный формат данных"},
                                         status=status.HTTP_400_BAD_REQUEST)
            except IntegrityError:
                return Response({"message": "Код элемента уже существует"},
                                         status=status.HTTP_400_BAD_REQUEST)
            return Response(EIGetSerializer(output).data, status=status.HTTP_201_CREATED)
        raise exc.ValidationError(serializer.errors)

    def patch(self, request, *args, **kwargs):
        serializer = EIUpdateSerializer(data=request.data)
        pk = kwargs.get('pk', False)
        if not pk:
            return Response({"message": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        try:
            element = self.queryset.get(pk=pk)
        except elements.Elements.DoesNotExist:
            return Response({"message": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        if serializer.is_valid():
            try:
                output = service.update_element_row(self.request.user, serializer.validated_data, element)
            except (dictionaries.Dictionaries.DoesNotExist, ElementIndicatorValues.DoesNotExist):
                return Response({"message": "Неверный code|id|type абстракции"},
                                         status=status.HTTP_400_BAD_REQUEST)
            except WrongType:
                return Response({"message": "Неверный тип значения"},
                                         status=status.HTTP_400_BAD_REQUEST)
            return Response(ElementSerializer(output).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        pk = kwargs.get('pk', False)
        if not pk:
            return Response({"message": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        try:
            element = self.queryset.get(pk=pk)
            element.delete()
        except elements.Elements.DoesNotExist:
            return Response({"message": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)
