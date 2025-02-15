from rest_framework import views
from rest_framework.response import Response
from pfbase.document.models.dynamic_doc import *
from pfbase.document.serializers.dynamic_doc import *
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser


class DynamicApiView(views.APIView):
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get(self, request, model_code):

        dynamic_model = DynamicModel(model_code)
        InvoiceSerializer = DynamicSerializer(model_code)

        qs = dynamic_model.objects.all()

        return Response({"count": qs.count(), "data": InvoiceSerializer(qs, many=True).data})

    def post(self, request, model_code):

        InvoiceSerializer = DynamicSerializer(model_code)
        dynamic_model = DynamicModel(model_code)
        serializer = InvoiceSerializer(data=request.data)

        if serializer.is_valid():
            with transaction.atomic():
                # Можете логику number сами придумать
                record = serializer.save(author=request.user, number="IND_12")
                qs = dynamic_model.objects.get(id=record.id)
            return Response(InvoiceSerializer(qs, many=False, partial=True).data, status=200)
        else:
            return Response(serializer.errors, status=400)

    def put(self, request, model_code, record_id):
        InvoiceSerializer = DynamicSerializer(model_code)
        dynamic_model = DynamicModel(model_code)

        instance = get_object_or_404(dynamic_model.objects.all(), id=record_id)

        serializer = InvoiceSerializer(instance, data=request.data, partial=True)

        if serializer.is_valid():
            with transaction.atomic():
                # Можете логику number сами придумать
                record = serializer.save(author=request.user, number="IND_12")
                qs = dynamic_model.objects.get(id=record.id)
            return Response(InvoiceSerializer(qs, many=False).data, status=200)
        else:
            return Response(serializer.errors, status=400)

    def delete(self, request, model_code, record_id):
        dynamic_model = DynamicModel(model_code)
        instance = get_object_or_404(dynamic_model.objects.all(), id=record_id)

        with transaction.atomic():
            dynamic_model.objects.delete_instance(instance)

        return Response(status=204)