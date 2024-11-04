from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from pfbase.pagination import CustomPagination
from ..serializers.eivalues import EIValuesSerializer
from ..models.eivalues import ElementIndicatorValues


class EIValuesAPIView(ModelViewSet):
    """
    Предтавление значения по :индикатору и :элементу
    """
    queryset = ElementIndicatorValues.objects.all().order_by('-id')
    serializer_class = EIValuesSerializer
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
        serializer = self.serializer_class(values, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='byindicator/(?P<indicator_id>\d+)')
    def byindicator(self, request, indicator_id=None):
        """
        Получения значений по :indicator_id
        """
        values = self.get_queryset().filter(indicator_id=indicator_id)
        if not values:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = self.serializer_class(values, many=True, context={'request': request})
        return Response(serializer.data)
