from rest_framework import status, views, exceptions as exc
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from pfbase.base_views import AbstractModelAPIView
from pfbase.pagination import CustomPagination
from ..serializers.elements import EIGetSerializer, EIPostSerializer, EIUpdateSerializer
from ..models import elements, dictionaries, indicators
from ...system.models import organization
from rest_framework.parsers import MultiPartParser, FormParser
from ..service import find_driver
import openpyxl


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
            serializer = EIGetSerializer(page, many=True, context={'request': request})
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
        return Response(EIGetSerializer(queryset, many=False, context={'request': request}).data)

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


class FileUploadView(views.APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request):
        uploaded_file = request.FILES.get('file')
        if not uploaded_file:
            return Response({"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            code = uploaded_file.name.split('_', 1)[-1].split('.')[0].strip()
            if not dictionaries.Dictionaries.objects.filter(code=code).exists():
                return Response({"error": f"Code '{code}' not found in the database"},
                                status=status.HTTP_404_NOT_FOUND)
            workbook = openpyxl.load_workbook(uploaded_file, data_only=True)

            if 'PF' not in workbook.sheetnames:
                return Response({"error": "Sheet 'PF' not found"}, status=status.HTTP_400_BAD_REQUEST)

            sheet = workbook['PF']
            headers = [cell for cell in next(sheet.iter_rows(min_row=1, max_row=1, values_only=True))]
            data = []

            for row in sheet.iter_rows(min_row=2, values_only=True):
                row_data = dict(zip(headers, row))
                code_el = row_data.get("CODE", "")
                org_code = row_data.get("ORGANIZATION.code")
                org_identifier = row_data.get("ORGANIZATION.identifier")

                organization_id = None
                if org_code:
                    organization_id = organization.Organization.objects.getByCode(org_code)
                elif org_identifier:
                    organization_id = organization.Organization.objects.getByIdentifier(org_identifier)

                if not organization_id:
                    continue
                short_name = {
                    "ru": row_data.get("SHORTNAME.ru", ""),
                    "kz": row_data.get("SHORTNAME.kz", ""),
                    "en": row_data.get("SHORTNAME.en", "")
                }

                dictionary_entry = dictionaries.Dictionaries.objects.getByCode(code)
                if not dictionary_entry:
                    continue

                dictionary_id = dictionary_entry
                indicators_list = []
                element_pod = None
                for header, value in row_data.items():
                    if header and header.startswith("IDC.") and value is not None:
                        parts = header.split('.')
                        if len(parts) >= 3:
                            ind_code = parts[1]
                            data_type = parts[2]
                            if data_type == "int":
                                ind_type = "int"
                            elif data_type == "str":
                                ind_type = "str"
                            elif data_type == "date":
                                ind_type = "date"
                            elif data_type == "time":
                                ind_type = "time"
                            elif data_type == "bool":
                                ind_type = "bool"
                            elif data_type == "float":
                                ind_type = "float"
                            elif data_type == "datetime":
                                ind_type = "datetime"
                            elif data_type == "text":
                                ind_type = "text"
                            elif data_type == "dct":
                                ind_type = "dct"
                            else:
                                continue
                            indicator_entry = indicators.DctIndicators.objects.getByCode(ind_code)
                            if header in "IDC.TRS_VEHCARD_CLASS.dct":
                                try:
                                    element_id = elements.Elements.objects.getByCode(value)
                                    if element_id:
                                        value = element_id
                                except elements.Elements.DoesNotExist:
                                    continue
                            elif header == "IDC.TRS_VEHCARD_NGDU.dct":
                                value = row_data.get("IDC.TRS_VEHCARD_NGDU.dct")

                            if indicator_entry:
                                indicators_list.append({
                                    "id": indicator_entry,
                                    "code": ind_code,
                                    "value": value,
                                    "type": ind_type,
                                })

                json_entry = {
                    "short_name": short_name,
                    "code": code_el,
                    "dictionary_id": dictionary_id,
                    "indicators": indicators_list,
                    "organization_id": organization_id,
                }

                data.append(json_entry)
            for entry in data:
                serializer = EIPostSerializer(data=entry, context={'request': request})
                if serializer.is_valid():
                    serializer.save()
                else:
                    return Response({"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
            return Response({"message": "All elements created successfully"}, status=status.HTTP_201_CREATED)

        except openpyxl.utils.exceptions.InvalidFileException:
            return Response({"error": "Invalid file format. Please upload a valid Excel file."},
                            status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)