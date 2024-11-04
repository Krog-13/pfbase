from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from pfbase.base_views import AbstractModelAPIView
from pfbase.pagination import CustomPagination
from ..serializers.listvalues import LValuesSerializer
from ..models.listvalues import ListValues


class LValuesAPIView(AbstractModelAPIView):
    """
    Представление спарвочника :Enum (до 50 значений)
    """
    queryset = ListValues.objects.all().order_by('-id')
    serializer_class = LValuesSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = CustomPagination

    @action(detail=False, methods=['get'], url_path='bylist/(?P<item>[^/.]+)')
    def bylist(self, request, item=None):
        """
        Получения ListValues по полю :list
        """
        enums = self.get_queryset().filter(list=item)
        if not enums:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = self.serializer_class(enums, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='bylistandcode/(?P<item>[^/.]+)/(?P<code>[^/.]+)')
    def bylistandcode(self, request, item=None, code=None):
        """
        Получения ListValues по полям :list & code
        """
        enums = self.get_queryset().filter(list=item, code=code)
        if not enums:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = self.serializer_class(enums, many=True, context={'request': request})
        return Response(serializer.data)
