"""
Abstract base views
"""
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import status
from django.db.models import Q


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

    @action(detail=False, methods=['get'], url_path='bychild/(?P<parent_id>[^/.]+)')
    def bychild(self, request, parent_id=None):
        """
        Получение дочерних объектов по :parent_id
        """
        dct_code = request.query_params.get('dct_code')
        search = request.query_params.get('search', '')
        print(self.basename)
        if self.basename == "elements":
            queryset = self.get_queryset().filter(Q(dictionary__code=dct_code) if dct_code else Q(),
                                                  parent_id=parent_id,
                                                  short_name__ru__icontains=search
                                                  )
        elif self.basename == "dictionaries":
            queryset = self.get_queryset().filter(Q(dictionary__code=dct_code) if dct_code else Q(),
                                                  parent_id=parent_id,
                                                  name__ru__icontains=search
                                                  )
        elif self.basename == "documents":
            queryset = self.get_queryset().filter(Q(dictionary__code=dct_code) if dct_code else Q(),
                                                  parent_id=parent_id,
                                                  name__ru__icontains=search
                                                  ).order_by("index_sort")
        else:
            queryset = self.get_queryset().filter(Q(dictionary__code=dct_code) if dct_code else Q())
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
