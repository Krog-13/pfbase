from rest_framework import status, views, exceptions as exc
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from pfbase.base_views import AbstractModelAPIView
from pfbase.pagination import CustomPagination
from ..serializers.elements import EIGetSerializer, EIPostSerializer, EIUpdateSerializer
from ..models import elements, Elements
from rest_framework.parsers import MultiPartParser, FormParser
from ..service import find_driver, upload_file, ExcelUpload, exist_element
from pfbase.exception import ExcelFormatError, WrongType


class ElementsAPIView(AbstractModelAPIView):
    """
    Представление :Element
    """
    queryset = elements.Elements.objects.all().order_by('-id')
    serializer_class = EIGetSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = CustomPagination

    @action(detail=False, methods=['get'], url_path='bydictionary/(?P<pk>\w+)')
    def bydictionary(self, request, pk=None):
        """
        Получения элементов по :pk ABCDictionary
        """
        user = request.user
        org = user.organization
        params = request.GET.copy()
        if pk.isdigit():
            dictionary = elements.Dictionaries.objects.get(pk=pk)
            params["DICT_CODE"] = dictionary.code
        else:
            params["DICT_CODE"] = pk
        organization_id = params.get("organization_id")
        if organization_id:
            params["organization_id"] = [organization_id]
        elif org:
            params["organization_id"] = [org.id]
        indicators = elements.Elements.objects.getByFilter(params)
        if_paginate = request.query_params.get('paginate', False)
        if if_paginate:
            serializer = EIGetSerializer(indicators, many=True, context={'request': request})
            return Response(serializer.data)
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
        element_values = exist_element(request.data)
        if element_values:
            return self._handle_patch(request, element_values.element_id)
        serializer = EIPostSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Element created successfully"},
                            status=status.HTTP_201_CREATED)
        raise exc.ValidationError(serializer.errors)

    def patch(self, request, *args, **kwargs):
        pk = kwargs.get('pk', False)
        if not pk:
            return Response({"message": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        return self._handle_patch(request, pk)

    def _handle_patch(self, request, pk):
        """Helper method to handle patch logic for a given pk."""
        try:
            element = self.queryset.get(pk=pk)
        except elements.Elements.DoesNotExist:
            return Response({"message": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = EIUpdateSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.update(element, serializer.validated_data)
            return Response({"message": "Element updated successfully"}, status=status.HTTP_200_OK)
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
            return Response({"error": "No file uploaded."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            json_entry_list,update_json_entry_list = upload_file(uploaded_file)
        except Exception as e:
            return Response({"error": f"Error processing file: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        if update_json_entry_list:
            for json_entry in update_json_entry_list:
                element = json_entry[0]
                serializer = EIUpdateSerializer(element, data=json_entry[1], partial=True,
                                                context={'request': request})
                if serializer.is_valid():
                    serializer.save()
                else:
                    return Response({"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        
        if json_entry_list:
            for json_entry in json_entry_list:
                serializer = EIPostSerializer(data=json_entry, context={'request': request})
                if serializer.is_valid():
                    serializer.save()
                else:
                    return Response({"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
                
        if json_entry_list is None and update_json_entry_list is None:
            return Response({"message": "No elements found in the file"}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({"message": "All elements processed successfully"}, status=status.HTTP_201_CREATED)

class FileUploadElementsView(views.APIView):
    """
    Upload excel file with elements
    """
    parser_classes = (MultiPartParser, FormParser)
    def post(self, request):
        user = request.user
        excel_file = request.FILES.get("file")
        trigger_param = request.data.get("trigger")
        checker = request.data.get("checker")
        if not excel_file:
            return Response({"error": "No file was uploaded. Please select a file and try again"}, status=400)
        try:
            excel_upload = ExcelUpload(excel_file, user, trigger_param, checker)
            excel_upload.check_format(excel_file)
            is_updated = excel_upload.start_upload()
        except ExcelFormatError:
            return Response({"error": "Invalid file format. Please upload an Excel file (.xls or .xlsx)."},
                            status=400)
        except Elements.DoesNotExist:
            return Response({"error": "Element does not exist"}, status=status.HTTP_400_BAD_REQUEST)
        except WrongType:
            return Response({"error": "Wrong type value or value format"}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        if is_updated == "create":
            return Response({"message": "All elements created successfully"}, status=status.HTTP_201_CREATED)
        elif is_updated == "update":
            return Response({"message": "All elements updated successfully"}, status=status.HTTP_200_OK)
        elif is_updated == "create_update":
            return Response({"message": "All elements created or updated successfully"}, status=status.HTTP_200_OK)
        elif is_updated == "create_skip":
            return Response({"message": "All elements created or skipped successfully"}, status=status.HTTP_200_OK)
        return Response({"warning": "Set params update!"}, status=400)
