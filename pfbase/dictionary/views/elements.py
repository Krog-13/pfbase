from rest_framework import status, views, exceptions as exc
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from pfbase.base_views import AbstractModelAPIView
from pfbase.pagination import CustomPagination
from ..serializers.elements import EIGetSerializer, EIPostSerializer, EIUpdateSerializer
from ..models import elements
from ..service import find_driver


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
        indicators = self.get_queryset().filter(dictionary_id=pk)
        page = self.paginate_queryset(indicators)
        if page is not None:
            serializer = EIGetSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        if not indicators:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = EIGetSerializer(indicators, many=True, context={'request': request})
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
            query_params = request.query_params
            code = kwargs.get('code', False)
            elements_queryset = self.queryset.filter(dictionary__code=code)
            instance = find_driver(elements_queryset, query_params)
            return Response(instance, status=status.HTTP_200_OK)
        try:
            queryset = self.queryset.get(id=pk)
        except elements.Elements.DoesNotExist:
            return Response({"message": "Element not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response(EIGetSerializer(queryset, many=False, context={'request':request}).data)

    def post(self, request):
        serializer = EIPostSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Element created successfully"},
                            status=status.HTTP_201_CREATED)
        raise exc.ValidationError(serializer.errors)

    def patch(self, request, *args, **kwargs):
        serializer = EIUpdateSerializer(data=request.data, context={'request': request})
        pk = kwargs.get('pk', False)
        if not pk:
            return Response({"message": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        try:
            element = self.queryset.get(pk=pk)
        except elements.Elements.DoesNotExist:
            return Response({"message": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        if serializer.is_valid():
            serializer.update(element, serializer.validated_data)
            return Response({"message": "Element updated successfully"})
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
