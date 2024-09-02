from rest_framework.generics import ListAPIView, UpdateAPIView, CreateAPIView
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, IsAdminUser
from rest_framework import status
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from .serializers import DictionarySerializer, IndicatorSerializer, \
    IndicatorValueSerializer, ElementSerializer, ElementSerializerSoft
from .models import Indicator, ElementIndicatorValue, ABCDictionary, Element
from .common import element_create


class ElementAPIView(ModelViewSet):
    """
    View for elements
    """
    queryset = Element.objects.all()
    serializer_class = ElementSerializer
    permission_classes = (IsAuthenticated,)

    def get_serializer_class(self):
        if self.request.query_params.get("soft"):
           return ElementSerializerSoft
        return ElementSerializer

    def get_queryset(self):
        """
        GET запрос для получения показателей по группе
        """
        dict_code = self.request.query_params.get('dict_code')
        parent = self.request.query_params.get('parent_id')
        queryset = super(ElementAPIView, self).get_queryset()
        if parent:
            return queryset.filter(parent=parent)
        try:
            abc_dict = ABCDictionary.objects.get(abc_code=dict_code)
        except ABCDictionary.DoesNotExist:
            abc_dict = None
        return queryset.filter(abc_dictionary=abc_dict)

    def get_object(self):
        pk = self.kwargs.get('pk')
        return Element.objects.get(id=pk)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        return Response(serializer.data)

    def create(self, request, *args, **kwargs):  # Todo: add create method
        pass




class ElementAPIViewOld(ListAPIView):
    """
    API для показателей
    """
    queryset = Element.objects.all()
    serializer_class = ElementSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        """
        GET запрос для получения показателей по группе
        """
        dict_code = self.request.query_params.get('dict_code')
        parent = self.request.query_params.get('parent_id')
        element = self.request.query_params.get('element_id')
        queryset = super(ElementAPIView, self).get_queryset()
        if parent:
            return queryset.filter(parent=parent)
        try:
            abc_dict = ABCDictionary.objects.get(abc_code=dict_code)
        except ABCDictionary.DoesNotExist:
            abc_dict = None
        if element:
            elements_ids = ElementIndicatorValue.objects.filter(indicator_value=element)
            column_values = elements_ids.values_list('element_id', flat=True)
            return queryset.filter(id__in=column_values)
        return queryset.filter(abc_dictionary=abc_dict)


class DictionaryAPIView(ListAPIView):
    """
    API для справочников
    """
    queryset = ABCDictionary.objects.all()
    serializer_class = DictionarySerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        """
        GET запрос для получения справочников по категории
        """
        # dictionary_id = self.request.user.organization_id
        category_id = self.request.query_params.get('category_id')
        if category_id:
            queryset = super(DictionaryAPIView, self).get_queryset()
            return queryset.filter(category_dictionary__id=category_id)
        else:
            queryset = super(DictionaryAPIView, self).get_queryset()
            return queryset.all()






class ElementChildAPIView(ListAPIView):
    """
    API для показателей
    """
    queryset = Element.objects.all()
    serializer_class = ElementSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        """
        GET запрос для получения показателей по группе
        """
        queryset = super(ElementChildAPIView, self).get_queryset()
        reference = self.request.query_params.get('reference_id')
        dictionary = self.request.query_params.get('dictionary_id', 0)
        element = self.request.query_params.get('element_id')
        indicator_id = Indicator.objects.filter(dictionary=reference, type_reference=dictionary).\
            values_list('id', flat=True).first()
        if indicator_id:
            elements_ids = ElementIndicatorValue.objects.filter(indicator_value=element, indicator=indicator_id)
            column_values = elements_ids.values_list('element_id', flat=True)
            return queryset.filter(id__in=column_values)
        return queryset.filter(abc_dictionary=reference)


class ElementListAPIView(ListAPIView):
    """
    API для показателей
    """
    queryset = Element.objects.all()
    serializer_class = ElementSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        """
        GET запрос для получения показателей по группе
        """
        queryset = super(ElementListAPIView, self).get_queryset()
        dict_code = self.request.query_params.get('dict_code')
        element = self.request.query_params.get('element_id', 0)
        try:
            abc_dict = ABCDictionary.objects.get(abc_code=dict_code)
        except ABCDictionary.DoesNotExist:
            abc_dict = None
        if element:
            elements_ids = ElementIndicatorValue.objects.filter(indicator_value=element)
            column_values = elements_ids.values_list('element_id', flat=True)
            return queryset.filter(id__in=column_values)
        return queryset.filter(abc_dictionary=abc_dict)


class DictIndicatorAPIView(ListAPIView):
    """
    API для показателей
    """
    queryset = Indicator.objects.all()
    serializer_class = IndicatorSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        """
        GET запрос для получения показателей по группе
        """
        queryset = super(DictIndicatorAPIView, self).get_queryset()
        return queryset.filter(dictionary=self.request.query_params["dictionary"])

    def create(self, request, *args, **kwargs):
        """
        POST запрос для создания значений показателей
        """
        element = request.data.get("element")
        indicator_value = request.data.get("indicator")
        return element_create(element, indicator_value)


class DictIndicatorDetailAPIView(ListAPIView,  CreateAPIView):
    """
    API для показателей
    """
    queryset = Indicator.objects.all()
    serializer_class = IndicatorSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        """
        GET запрос для получения показателей по группе
        """
        dictionary_id = self.request.query_params.get('dictionary_id')
        queryset = super(DictIndicatorDetailAPIView, self).get_queryset()
        return queryset.filter(dictionary=dictionary_id)

    def create(self, request, *args, **kwargs):
        """
        POST запрос для создания значений показателей
        """
        element = request.data.get("element")
        indicator_value = request.data.get("indicator")
        return element_create(element, indicator_value)


class DictIndicatorValueAPIView(ListAPIView, CreateAPIView, UpdateAPIView):
    """
    API для значений показателей
    """
    queryset = ElementIndicatorValue.objects.all()
    serializer_class = IndicatorValueSerializer
    permission_classes = (IsAuthenticated,)

    def create(self, request, *args, **kwargs):
        """
        POST запрос для создания значений показателей
        """
        new_data = request.data.get("values", [])
        # return element_create(new_data)

    def get_queryset(self):
        """
        GET запрос для получения выходных справочников по справочнику
        """
        queryset = super(DictIndicatorValueAPIView, self).get_queryset()
        element_id = self.request.query_params.get("element_id")
        abc_code = self.request.query_params.get("abc_code")

        return queryset.filter(element_id=element_id, element__abc_dictionary__abc_code=abc_code)

    # def get(self, request, *args, **kwargs):
    #     """
    #     GET запрос для получения значений показателей по выходному справочнику
    #     """
    #     output_id = self.request.query_params.get('output_id')
    #     indicator_values = DictionaryIndicatorValue.objects.filter(
    #         output_dictionary_id=output_id)
    #     serializer = IndicatorValueSerializer(indicator_values, many=True)
    #     return Response(serializer.data)


class GetVatView(ListAPIView):
    """
    API для получения НДС
    """
    queryset = ElementIndicatorValue.objects.all()
    serializer_class = IndicatorValueSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        """
        GET запрос для получения НДС
        """
        queryset = super(GetVatView, self).get_queryset()
        abc_vat = ABCDictionary.objects.get(abc_code=400)
        year = self.request.query_params.get("year")
        return queryset.filter(element__abc_dictionary=abc_vat, element__short_name__contains=year)

# class OutputExportAPIView(CreateAPIView):
#     queryset = OutputReport.objects.all()
#     serializer_class = OutputReportSerializer
#     permission_classes = (IsAuthenticated,)

#     def create(self, request, *args, **kwargs):

#         output_report = OutputReport.objects.get(
#             id=self.request.data["output_id"])
#         return get_table(output_report)


# class InputFileAPIView(CreateAPIView):
#     permission_classes = (IsAuthenticated,)
#     queryset = OutputReport.objects.all()
#     serializer_class = OutputReportSerializer

#     def get(self, request, *args, **kwargs):
#         filename = "out_sample.pdf"
#         file_id = "d1685144632e4745bc44b42e97c56676"
#         return get_file_minio(file_id, filename)

#     def post(self, request, *args, **kwargs):
#         report = OutputReport.objects.get(id=request.data["output_id"])
#         excel_file = request.FILES.get('file')
#         file_id = uuid4().hex
#         save_file_minio(excel_file, file_id)
#         obj = Indicator.objects.get(id=request.data["indicator_id"])
#         json_data = IndicatorValue.json_file_data(excel_file.name, file_id)
#         IndicatorValue.objects.create(
#             indicator_value=json_data, indicator=obj, output_report=report)
#         return Response({}, status=status.HTTP_201_CREATED)


# class InputImportAPIView(CreateAPIView):
#     permission_classes = (IsAuthenticated,)

#     def post(self, request, *args, **kwargs):
#         excel_file = request.FILES.get('file')
#         report_id = self.request.data["report_id"]
#         return get_excel_data(excel_file, report_id)


# class DownloadTeamplateAPIView(ListAPIView):
#     permission_classes = (IsAuthenticated,)

#     def get(self, request, *args, **kwargs):
#         report_id = self.request.query_params['report_id']
#         return get_download_file(report_id)


# class DownloadInstrutionsAPIView(ListAPIView):
#     permission_classes = (IsAuthenticated,)

#     def get(self, request, *args, **kwargs):

#         report_id = self.request.query_params.get('report_id')
#         instruction = True
#         return get_download_file(report_id, instruction)
