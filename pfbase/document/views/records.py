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
from django.db.models import OuterRef, Prefetch, Subquery
from pfbase.pagination import CustomPagination
from ..common import prepare_records
from ..serializers.records import RIGetSerializer, RecordDetailSerializer, RecordPostSerializer, RecordUpdateSerializer, RecordSerializer, \
    RecordPackUpdateSerializer, RecordListUpdateSerializer, RecordsSerializer
from ..models.records import Records
from ..models.rhistory import RecordHistory
from ..models.indicators import DcmIndicators
from ..tools import build_records_table
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from pfbase.permissions import RecordPermissions


class RecordAPIView(ModelViewSet):
    """
    Представление :Record
    """
    queryset = Records.objects.all().order_by('-id')
    serializer_class = RIGetSerializer
    permission_classes = (RecordPermissions,)
    pagination_class = CustomPagination

    @action(detail=False, methods=['get'], url_path='bydocument/(?P<pk>\w+)')
    def bydocument(self, request, pk=None):
        """
        Получения записей по :pk Document
        """
        if pk.isdigit():
            indicators = self.get_queryset().filter(document_id=pk)
        else:
            indicators = self.get_queryset().filter(document__code=pk)
        if not indicators:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = self.serializer_class(indicators, many=True, context={'request': request})
        return Response(serializer.data)


class RIAPIView(views.APIView):
    """
    Представление :Record with their :Indicators
    """
    queryset = Records.objects.all().order_by('-created_at', '-id')
    permission_classes = (IsAuthenticated,)
    pagination_class = CustomPagination
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get(self, request, *args, **kwargs):
        record_id = kwargs.get("pk")
        if record_id:
            record = Records.objects.select_related(
                "document", "author", "organization", "parent"
            ).prefetch_related(
                "record_values__indicator",
                Prefetch(
                    "history",
                    queryset=RecordHistory.objects.select_related("status").order_by("-created_at", "-id"),
                    to_attr="prefetched_history",
                ),
            ).filter(pk=record_id).first()
            if record is None:
                return Response({"message": "Record not found"}, status=status.HTTP_404_NOT_FOUND)
            data = RecordDetailSerializer(record, context={"request": request}).data
            return Response(data, status=status.HTTP_200_OK)

        document_code = request.query_params.get("document_code")
        if not document_code:
            return Response(
                {"message": "Query parameter 'document_code' is required."},
                status=status.HTTP_400_BAD_REQUEST)

        raw_codes = request.query_params.getlist("indicators_code")
        indicator_codes = [
            code.strip()
            for raw_code in raw_codes
            for code in raw_code.split(",")
            if code.strip()
        ]
        if not indicator_codes:
            indicator_codes = list(
                DcmIndicators.objects.filter(document__code=document_code)
                .order_by("index_sort", "id")
                .values_list("code", flat=True)
            )
        records = prepare_records(self.queryset, document_code, indicator_codes)

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(records, request, view=self)
        output = build_records_table(page, request.query_params, document_code, indicator_codes)

        return Response(
            {
                "count": paginator.page.paginator.count,
                "total_pages": paginator.page.paginator.num_pages,
                "next": paginator.get_next_link(),
                "previous": paginator.get_previous_link(),
                **output,
            }, status=status.HTTP_200_OK)

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
        output = RecordsSerializer(out, many=True, context={'request': request})
        return Response(output.data, status=status.HTTP_200_OK)
