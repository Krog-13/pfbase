from rest_framework import views
from rest_framework.response import Response
from pfbase.document.serializers.business import *
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from pfbase.pagination import CustomPagination

"""
Данный класс яляется лишь примером для использования Бизнес-моделей и Бизнес-сериалайзера.
Пример служит для более легкого ориентирования в при кодинге.
"""


class BusinessModelApiView(views.APIView):
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    permission_classes = (IsAuthenticated, IsAdminUser)
    pagination_class = CustomPagination

    def get(self, request, model_code):
        BusinessSerializer = BusinessDocumentModelSerializer(model_code)
        queryset = BusinessDocumentModel(model_code)

        qs = queryset.objects.all().select_related('author', 'organization', 'parent', 'document').order_by('-id')
        serializer = BusinessSerializer(qs, many=True).only_fields('number', 'TEST_IND_FILE').set_required()
        return Response(serializer.data)

    def post(self, request, model_code):
        BusinessSerializer = BusinessDocumentModelSerializer(model_code)
        business_model = BusinessDocumentModel(model_code)
        serializer = BusinessSerializer(data=request.data)

        if serializer.is_valid():
            with transaction.atomic():
                # Можете логику number сами придумать
                record = serializer.save(author=request.user, number="IND_12")
                qs = business_model.objects.get(id=record.id)
            return Response(BusinessSerializer(qs, many=False, partial=True).data, status=200)
        else:
            return Response(serializer.errors, status=400)

    def put(self, request, model_code, record_id):
        with transaction.atomic():
            BusinessSerializer = BusinessDocumentModelSerializer(model_code)
            business_model = BusinessDocumentModel(model_code)

            instance = get_object_or_404(business_model.objects.all(), id=record_id)

            serializer = BusinessSerializer(instance, data=request.data, partial=True)

            if serializer.is_valid():
                with transaction.atomic():
                    # Можете логику number сами придумать
                    record = serializer.save(author=request.user, number="IND_12")
                    qs = business_model.objects.get(id=record.id)

                return Response(BusinessSerializer(qs, many=False).data, status=200)
            else:
                return Response(serializer.errors, status=400)

    def delete(self, request, model_code, record_id):
        business_model = BusinessDocumentModel(model_code)
        instance = get_object_or_404(business_model.objects.all(), id=record_id)

        with transaction.atomic():
            business_model.objects.delete_instance(instance)

        return Response(status=204)


class BusinessModelIndListApiView(views.APIView):
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    permission_classes = (IsAuthenticated, IsAdminUser)
    pagination_class = CustomPagination

    def get(self, request, model_code):
        BusinessSerializer = BusinessDocumentModelSerializer(model_code)
        queryset = BusinessDocumentModel(model_code)
        qs = queryset.objects.all().select_related('author', 'organization', 'parent', 'document')

        serializer = BusinessSerializer(qs, many=True).get_details()
        return Response(serializer.data)