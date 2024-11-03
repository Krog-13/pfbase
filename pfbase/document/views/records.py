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
from rest_framework import status, views, generics, exceptions as exc
from pfbase.pagination import CustomPagination
from ..serializers.records import RIGetSerializer, RecordPostSerializer, RecordUpdateSerializer, RecordSerializer, \
    RecordPackUpdateSerializer, RecordListUpdateSerializer, RecordsSerializer
from ..models.records import Records
from ..service import table_present


class RecordAPIView(ModelViewSet):
    """
    Представление :Record
    """
    queryset = Records.objects.all().order_by('-id')
    serializer_class = RIGetSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = CustomPagination

    @action(detail=False, methods=['get'], url_path='bydocument/(?P<pk>\d+)')
    def bydocument(self, request, pk=None):
        """
        Получения записей по :pk Document
        """
        indicators = self.get_queryset().filter(document_id=pk)
        if not indicators:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = self.serializer_class(indicators, many=True)
        return Response(serializer.data)


class RIAPIView(views.APIView):
    """
    Представление :Record with their :Indicators
    """
    queryset = Records.objects.all().order_by('-created_at')
    permission_classes = (IsAuthenticated,)
    pagination_class = CustomPagination

    def get(self, request, *args, **kwargs):
        pk = kwargs.get('pk', False)
        if not pk:
            records = self.queryset.all()
            query_params = request.query_params
            output = table_present(records, query_params)
            return Response(output, status=status.HTTP_200_OK)
        try:
            queryset = self.queryset.get(id=pk)
        except Records.DoesNotExist:
            return Response({"message": "Record not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response(RIGetSerializer(queryset, many=False).data)

    def post(self, request):
        serializer = RecordPostSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Record created successfully"},
                            status=status.HTTP_201_CREATED)
        raise exc.ValidationError(serializer.errors)

    def patch(self, request, *args, **kwargs):
        serializer = RecordListUpdateSerializer(data=request.data, context={'request': request})
        pk = kwargs.get('pk', False)
        if pk:
            return Response({"message": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        try:
            record = self.queryset.first()
        except Records.DoesNotExist:
            return Response({"message": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        if serializer.is_valid():
            serializer.update(record, serializer.validated_data)
            return Response({"message": "Record updated successfully"})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        pk = kwargs.get('pk', False)
        if not pk:
            return Response({"message": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        try:
            record = self.queryset.get(pk=pk)
            record.soft_delete()
        except Records.DoesNotExist:
            return Response({"message": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)


class RecordIndicator(generics.ListAPIView):
    """
    Представление :Record with their :Indicators
    """
    queryset = Records.objects.all().order_by('-created_at')
    serializer_class = RecordSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = CustomPagination

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        query_param = request.query_params.get('indicator', None)

        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data)


class TestApiView(views.APIView):
    """
    Представление :Record with their :Indicators
    """
    permission_classes = (IsAuthenticated,)
    pagination_class = CustomPagination

    def get(self, request, *args, **kwargs):
        # output = self.queryset.obj getByFilter({"id": 45})
        query_params = request.query_params
        out = Records.objects.getByFilter(query_params)
        output = RecordsSerializer(out, many=True)
        return Response(output.data, status=status.HTTP_200_OK)
