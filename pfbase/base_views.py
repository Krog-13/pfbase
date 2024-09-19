"""
Abstract base views
"""
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import status


class AbstractModelAPIView(ModelViewSet):
    """
    Базовый класс представлений
    """
    @action(detail=False, methods=['get'], url_path='bycode/(?P<code>[^/.]+)')
    def bycode(self, request, code=None):
        """
        Получения объекта по :code
        """
        instance = self.get_queryset().filter(code=code).first()
        if not instance:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
