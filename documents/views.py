import json
from uuid import uuid4

from django.http import QueryDict
from django.shortcuts import get_object_or_404
from rest_framework.filters import OrderingFilter
from rest_framework.generics import ListAPIView, UpdateAPIView, CreateAPIView, RetrieveUpdateAPIView, ListCreateAPIView
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.renderers import TemplateHTMLRenderer, JSONRenderer
from rest_framework.viewsets import ViewSet, ModelViewSet
from rest_framework.views import APIView
from .models import Record, ABCDocument, RecordIndicatorValue, RecordHistory, Indicator
from .serializers import  DocumentSerializer, FieldSerializer,\
    FieldValueSerializer, JournalDocumentSerializer, JournalHistorySerializer, JournalDetailSerializer, JournalSerializer, JournalSerializer2, JournalModelSerializer, JournalModelVacancySerializer
from .common import journal_create, journal_history_create, indicator_create, download_file,\
    upload_file, save_file_minio, get_documents_id, journal_update, update_file, indicator_update, get_file_object,\
    get_file_object_super, journal_vac_create, journal_vac_update
from rest_framework import status, generics
from django.views.generic import TemplateView
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from django.db.models import Max
from django.db.models import Q
from rest_framework.filters import SearchFilter
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from IEF.mail_notificatoin import send_notification_email, send_approve_users
from .permissions import IsOwnerOrReadOnly, IsAdminReadOnly
from rest_framework import permissions


class CustomPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class DocumentFieldAPIView(ListAPIView):
    """
    API для полей документа
    """
    queryset = Indicator.objects.all()
    serializer_class = FieldSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        """
        GET запрос для получения полей по группе
        """
        queryset = super(DocumentFieldAPIView, self).get_queryset()
        abc_code = self.request.query_params.get("abc_code")
        # return queryset.filter(document__abc_code=abc_code)
        return queryset.filter(document__abc_code__in=abc_code.split(","))


class DocumentValueAPIView(ListAPIView, UpdateAPIView):
    queryset = RecordIndicatorValue.objects.all()
    serializer_class = FieldValueSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        """
        GET запрос для получения выходных справочников по справочнику
        """
        queryset = super(DocumentValueAPIView, self).get_queryset()
        journal_id = self.request.query_params.get("journal_id")
        abc_document_id = self.request.query_params.get("abc_document_id")
        if abc_document_id:
            return queryset.filter(journal_document__abc_document_id=abc_document_id)
        return queryset.filter(journal_document__parent=journal_id)


class JournalViewSet(ViewSet):
    """
    ViewSet for Journal
    """
    queryset = Record.objects.all()
    serializer_class = JournalSerializer
    permission_classes = (IsAuthenticated, IsOwnerOrReadOnly)
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_serializer_class(self):
        if self.request.method in permissions.SAFE_METHODS:
            return JournalModelSerializer
        return JournalSerializer

    def retrieve(self, request):
        user = request.user
        journal_code = request.query_params.get("journal_code")
        try:
            queryset = self.queryset.get(author=user, abc_document__abc_code=journal_code)  # use get for one object
        except Record.DoesNotExist:
            return Response({"message": "Journal not found"}, status=404)
        self.check_object_permissions(request, queryset)
        serializer = self.get_serializer_class()(queryset, many=False)  # set many=True for list
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        rq_data = request.data
        upload_files = request.FILES
        files = dict()
        # upload_files = request.FILES.getlist("files") # together files one pack
        if isinstance(rq_data, QueryDict):
            rq_str_data = request.data.get("data", {})
            rq_data = json.loads(rq_str_data)

        for data in rq_data.get("data"):
            if upload_files:
                file_objects = get_file_object(data, upload_files)
                for file in file_objects:
                    file_name = save_file_minio(file[1])
                    files[file[0]] = file_name[0]  # key = code, value = file's name
                    # file_meta = ';'.join(file_name)
            journal_create(data, request.user, files)
        return Response("Journal created", status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        rq_data = request.data
        upload_files = request.FILES
        if isinstance(rq_data, QueryDict):
            rq_str_data = request.data.get("data", {})
            rq_data = json.loads(rq_str_data)

        for data in rq_data.get("data"):
            file_meta = None
            if upload_files:
                file_obj = get_file_object(data, upload_files)
                if file_obj:
                    file_name = save_file_minio(file_obj)
                    file_meta = ';'.join(file_name)
            journal_update(data, request.user, file_meta)
        return Response("Journal created", status=status.HTTP_201_CREATED)


class DocumentVacancyAPIView(CreateAPIView, UpdateAPIView, ListAPIView):
    queryset = Record.objects.all()
    serializer_class = JournalModelVacancySerializer
    permission_classes = (IsAuthenticated, IsOwnerOrReadOnly)

    def get_queryset(self):
        """
        GET journal vacancy with stage
        """
        queryset = super(DocumentVacancyAPIView, self).get_queryset()
        journal_code = self.request.query_params.get("journal_code")
        try:
            queryset = queryset.filter(author=self.request.user, abc_document__abc_code=journal_code)
        except Record.DoesNotExist:
            return Response({"message": "Journal not found"}, status=404)
        return queryset

    def create(self, request, *args, **kwargs):
        """POST"""
        rq_data = request.data
        journal_vac_create(rq_data, request.user)
        return Response("Journal created", status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        """PATCH"""
        rq_data = request.data
        journal_vac_update(rq_data, request.user)
        return Response("Journal created", status=status.HTTP_201_CREATED)


class DocumentAPIView(ListAPIView):
    """
    API для документов
    """
    queryset = ABCDocument.objects.all()
    serializer_class = DocumentSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        """
        GET запрос для получения документов по категории
        """
        document_id = self.request.user.organization_id
        category_id = self.request.query_params.get('category_id')
        if category_id:
            queryset = super(DocumentAPIView, self).get_queryset()
            return queryset.filter(category_document__id=category_id, organizations=document_id)
        else:
            queryset = super(DocumentAPIView, self).get_queryset()
            return queryset.filter(organizations=document_id)


class JournalValueAPIView(CreateAPIView, UpdateAPIView):
    """"""
    queryset = RecordIndicatorValue.objects.all()
    serializer_class = JournalDetailSerializer
    permission_classes = (IsAuthenticated,)

    def create(self, request, *args, **kwargs):
        """
        POST запрос для создания значений показателей
        """
        journal_id = request.data.get("journal_id")
        indicator_value = request.data.get("indicator")
        try:
            return indicator_create(journal_id, indicator_value)
        except Exception:
            return Response({"Msg": "Something wrong please correction your query!"},
                     status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        journal_id = self.request.data.get('journal_id')
        indicator = self.request.data.get('indicator')
        # user_id = self.request.user.id
        try:
            return indicator_update(journal_id, indicator)
        except Exception:
            return Response({"Msg": "Something wrong please correction your query!"},
                            status=status.HTTP_400_BAD_REQUEST)


class JournalDetailAPIViewOLD(ListAPIView):
    """"""
    queryset = Record.objects.all()
    serializer_class = JournalDetailSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        journal = self.request.query_params.get('journal_id')
        parent_id = self.request.query_params.get('parent_id')
        queryset = super(JournalDetailAPIViewOLD, self).get_queryset()
        if parent_id:
            return queryset.filter(parent=parent_id)
        return queryset.filter(id=journal)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


class DocumentFileAPIView(ListAPIView, CreateAPIView, UpdateAPIView):
    """CRUD file"""
    queryset = Record.objects.all()
    permission_classes = (IsAuthenticated, IsOwnerOrReadOnly)
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get(self, request, *args, **kwargs):
        """Download file"""
        value_id = self.request.query_params['field_value_id']
        return download_file(value_id)

    def update(self, request, *args, **kwargs):
        uploaded_file = request.FILES.get('file')
        field_id = request.data.get('field_value_id')
        try:
            queryset = self.queryset.get(author=request.user, field_value=field_id)  # use get for one object
        except Record.DoesNotExist:
            return Response({"message": "Journal not found"}, status=404)
        self.check_object_permissions(request, queryset)
        if uploaded_file:
            files_naming = save_file_minio(uploaded_file)
            id_files = ';'.join(files_naming)
            try:
                return update_file(field_id, id_files)
            except Exception:
                return Response({"Msg": "Something wrong please correction your query!"},
                         status=status.HTTP_400_BAD_REQUEST)
        return Response({"Msg": "File not selected"},
                        status=status.HTTP_204_NO_CONTENT)


class JournalDocumentFindAPIView(ListAPIView):
    """
    API для поиска документов
    """
    queryset = Record.objects.all()
    serializer_class = JournalDocumentSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = CustomPagination

    def get_queryset(self):
        """
        GET запрос для поиска документов
        """
        search = self.request.query_params.get('search')
        queryset = super(JournalDocumentFindAPIView, self).get_queryset()
        return queryset.filter(short_name__icontains=search)


class JournalDocumentStatusAPIView(ListAPIView, CreateAPIView):
    """
    API journal status
    """
    queryset = Record.objects.all()
    serializer_class = JournalDocumentSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = CustomPagination

    def get_queryset(self):
        """
        GET
        """
        code_date_from = 102
        code_date_to = 103
        status = self.request.query_params.get('status')
        queryset = super(JournalDocumentStatusAPIView, self).get_queryset()
        date_from = RecordIndicatorValue.objects.filter(journal_document__abc_document__abc_code=801,
                                              indicator__idc_code__in=(code_date_from, code_date_to)).values('journal_document_id','indicator_value', 'indicator__idc_code')
        res = get_documents_id(date_from, status)
        if status == "active":
            return queryset.filter(id__in=res['active'])
        elif status == "inactive":
            return queryset.filter(id__in=res['inactive'])


class JournalUpdateAPIView(RetrieveUpdateAPIView):
    queryset = Record.objects.all()
    serializer_class = JournalSerializer
    # permission_classes = (IsOwnerOrReadOnly,)
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]

    def get_serializer_class(self):
        print("get serialier")
        if self.request.user.is_staff:
            return JournalSerializer
        return JournalSerializer2
    def get_serializer(self, *args, **kwargs):
        pass

    def get_object(self):
        obj = get_object_or_404(self.queryset, pk=self.kwargs["pk"])
        chedkc = self.check_object_permissions(self.request, obj)
        # self.check_permissions(self.request)
        return obj

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        data = {"user": self.object, "message": "Hello wo"}
        # return Response({"user": self.object}, template_name='user.html')
        return Response(data, template_name='user.html')


class JournalModeViewSetOld(ViewSet):
    """
    API для журнала
    """
    queryset = Record.objects.all()
    serializer_class = JournalSerializer

    def get_object(self):
        obj = get_object_or_404(self.queryset, pk=self.kwargs["pk"])
        self.check_object_permissions(self.request, obj)
        print("test get object")
        return obj

    def list(self, request, *args, **kwargs):
        queryset = self.get_object()
        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data)

    def put(self, request, *args, **kwargs):
        instance = Record.objects.get(id=114)
        serializer = JournalSerializer(data=request.data, instance=instance)
        serializer.is_valid()
        serializer.save()
        return Response({"post": serializer.data})


class JournalModeViewSet2(ModelViewSet):
    """
    API для журнала
    """
    queryset = Record.objects.all()
    serializer_class = JournalSerializer
    # permission_classes = (IsOwnerOrReadOnly, IsAdminReadOnly)

    def get_object(self):
        obj = get_object_or_404(self.get_queryset(), pk=self.kwargs["pk"])
        self.check_object_permissions(self.request, obj)
        return obj


    def put(self, request, *args, **kwargs):
        user = request.user
        auth = request.auth
        print(user, auth)
        instance = Record.objects.get(id=114)
        serializer = JournalSerializer(data=request.data, instance=instance)
        serializer.is_valid()
        serializer.save()
        return Response({"post": serializer.data})

    # permission_classes = (IsOwnerOrReadOnly)

    # def get_queryset(self):
    #     """
    #     GET запрос для получения журнала
    #     """
    #     queryset = super(JournalModeViewSet, self).get_queryset()
    #     return queryset.all()

    # def list(self, request):
    #     queryset = self.queryset.all()
    #     serializer = self.serializer_class(queryset, many=True)
    #     return Response(serializer.data)
    #
    # def retrieve(self, request, pk=None):
    #     queryset = JournalDocument.objects.all()
    #     journal = get_object_or_404(queryset, pk=pk)
    #     serializer = JournalSerializer(journal)
    #     return Response(serializer.data)
    #
    # def create(self, request):
    #     serializer = self.serializer_class(data=request.data)
    #     if serializer.is_valid():
    #         serializer.save()
    #         return Response(serializer.data, status=status.HTTP_201_CREATED)
    #     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    #
    # def update(self, request, pk=None):
    #     journal = self.queryset.get(pk=pk)
    #     serializer = self.serializer_class(journal, data=request.data)
    #     if serializer.is_valid():
    #         serializer.save()
    #         return Response(serializer.data)
    #     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    #
    # def destroy(self, request, pk=None):
    #     journal = self.queryset.get(pk=pk)
    #     journal.delete()
    #     return Response(status=status.HTTP_204_NO_CONTENT)


class JournalListAPIView(ListCreateAPIView):
    queryset = Record.objects.all()
    serializer_class = JournalSerializer
    permission_classes = (IsOwnerOrReadOnly, IsAdminReadOnly)
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    search_fields = ['short_name', 'doc_number'] # поиск по полям
    ordering_fields = ['short_name', "created_at"]
    filterset_fields = ['doc_number', 'short_name']

    def get_object(self):
        print("test tt")
        obj = get_object_or_404(self.get_queryset(), pk=114)
        self.check_object_permissions(self.request, obj)
        print("test get object")
        return obj

    # def get_queryset(self):
    #     queryset = super(JournalListAPIView, self).get_queryset()
    #     return queryset.all()

    def list(self, request, *args, **kwargs):
        queryset = self.get_object()
        serializer = JournalSerializer(queryset, many=False)
        return Response(serializer.data)

    # def get(self, request, *args, **kwargs):
    #     status = self.request.query_params.get("status", None)
    #     queryset = JournalDocument.objects.all()
    #     if status is not None:
    #         queryset = queryset.filter(doc_number=status)
    #     else:
    #         queryset = self.queryset
    #     return Response(self.serializer_class(queryset, many=True).data)
        # user = request.user
        # queryset = self.queryset.filter(author=user)
        # return Response(self.serializer_class(queryset, many=True).data)

    # def list(self, request, *args, **kwargs):
    #     queryset = self.queryset.all()
    #     # print(queryset1)
    #     # queryset = self.get_queryset()
    #     serializer = self.serializer_class(queryset, many=True)
    #     return Response(serializer.data)

class JournalUpdate2APIView(UpdateAPIView):
    queryset = Record.objects.all()
    serializer_class = JournalSerializer
    permission_classes = (IsOwnerOrReadOnly,)

    # def update(self, request, *args, **kwargs):
    #     journal = self.request.data.get('journal')
    #     indicator = self.request.data.get('indicator')
    #     user_id = self.request.user.id
    #     try:
    #         return journal_update(journal, indicator, user_id)
    #     except Exception:
    #         return Response({"Msg": "Something wrong please correction your query!"},
    #                  status=status.HTTP_400_BAD_REQUEST)
    #
    # def delete(self, request, *args, **kwargs):
    #     """
    #     Delete
    #     """
    #     journal = self.request.query_params.get('journal_id')
    #     try:
    #         obj = JournalDocument.objects.get(id=journal)
    #         obj.delete()
    #     except JournalDocument.DoesNotExist:
    #         return Response({"message": f"Jornal by ID - {journal} dose not exist!"}, status=404)
    #     return Response({"message": "Object deleted successfully"}, status=204)


class JournalAPIView(APIView):
    """API"""
    permission_classes = (IsAdminReadOnly, IsOwnerOrReadOnly)

    def get(self, request, pk):
        """
        GET запрос для получения журнала
        """
        journal = get_object_or_404(Record, id=pk)
        serializer = JournalDocumentSerializer(journal)
        return Response(serializer.data)

    def put(self, request, pk):
        """
        PUT запрос для обновления журнала
        """
        journal = get_object_or_404(Record, id=pk)
        serializer = JournalSerializer(journal, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class JournalDocumentUpdateAPIView(generics.RetrieveUpdateAPIView):
    """API Update Journal Document"""
    queryset = Record.objects.all()
    serializer_class = JournalDocumentSerializer
    permission_classes = (IsOwnerOrReadOnly,)

    def update(self, request, *args, **kwargs):
        journal = self.request.data.get('journal')
        indicator = self.request.data.get('indicator')
        user_id = self.request.user.id
        try:
            return journal_update(journal, indicator, user_id)
        except Exception:
            return Response({"Msg": "Something wrong please correction your query!"},
                     status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        """
        Delete
        """
        journal = self.request.query_params.get('journal_id')
        try:
            obj = Record.objects.get(id=journal)
            obj.delete()
        except Record.DoesNotExist:
            return Response({"message": f"Jornal by ID - {journal} dose not exist!"}, status=404)
        return Response({"message": "Object deleted successfully"}, status=204)




class JournalDocumentAPIView(ListAPIView, CreateAPIView, UpdateAPIView):
    """
    API для показателей
    """
    queryset = Record.objects.all().order_by("id")
    serializer_class = JournalDocumentSerializer
    permission_classes = (IsOwnerOrReadOnly,)
    pagination_class = CustomPagination
    filter_backends = [OrderingFilter]
    ordering_fields = ['short_name', "created_at"]

    def get_queryset(self):
        """
        GET запрос для получения показателей по группе
        """
        code_date_from = 102
        code_date_to = 103
        document = self.request.query_params.get('document_id')
        parent = self.request.query_params.get('parent_id', '')
        journal = self.request.query_params.get('journal_id')
        status = self.request.query_params.get('status', '')
        search = self.request.query_params.get('search', '')
        queryset = super(JournalDocumentAPIView, self).get_queryset()
        date_from = RecordIndicatorValue.objects.filter(journal_document__abc_document__abc_code=801,
                                              indicator__idc_code__in=(code_date_from, code_date_to)).values(
            'journal_document_id', 'indicator_value', 'indicator__idc_code')
        res = get_documents_id(date_from, status)
        if status == "active":
            return queryset.filter(id__in=res['active'])
        elif status == "inactive":
            return queryset.filter(id__in=res['inactive'])

        queryset = super(JournalDocumentAPIView, self).get_queryset()
        queryset = queryset.annotate(
            latest_history_status_id=Max('history_status__id'))
        latest_history_statuses = queryset.values('id', 'latest_history_status_id').distinct()
        if parent:
            return queryset.filter(parent=parent)
        elif document and status != 'all' and status:
            return queryset.filter(history_status__id__in=latest_history_statuses.values('latest_history_status_id'),
                                   history_status__journal_status=status, abc_document=document)
        elif document:
            return queryset.filter(Q(short_name__icontains=search) | Q(doc_number__icontains=search), abc_document=document,)
        elif journal:
            return queryset.filter(id=journal)
        elif status:
            return queryset.filter(history_status__id__in=latest_history_statuses.values('latest_history_status_id'),
                                   history_status__journal_status=status)
        else:
            return queryset.all()

    def create(self, request, *args, **kwargs):
        """
        POST запрос для создания значений показателей
        """
        uploaded_files = request.FILES.getlist('files')
        uploaded_file = request.data.get('file', None)
        json_data = request.data.get('data', {})
        if not json_data:
            indicator_value = self.request.data.get('indicator')
            element = self.request.data.get('journal')
        else:
            response_data = json.loads(json_data)
            element = response_data.get("journal")
            indicator_value = response_data.get("indicator")

        files_naming = ""
        file_order = ""
        if uploaded_files:
            output = save_file_minio(uploaded_files)
            files_naming = ';'.join(output)
        if uploaded_file:
            if uploaded_file != "null":
                output = save_file_minio(uploaded_file)
                file_order = ';'.join(output)
        user = request.user
        try:
            return journal_create(element, indicator_value, user, files_naming, file_order)
        except Exception:
            return Response({"Msg": "Something wrong please correction your query!"},
                     status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        """
        Delete
        """
        journal = self.request.query_params.get('journal_id')
        try:
            obj = Record.objects.get(id=journal)
            obj.soft_delete()
        except Record.DoesNotExist:
            return Response({"message": f"Jornal by ID - {journal} dose not exist!"}, status=404)
        return Response({"message": "Object deleted successfully"}, status=204)

    def update(self, request, *args, **kwargs):
        """Restore object"""
        journal = self.request.query_params.get('journal_id')
        try:
            obj = Record.everything.get(id=journal)
            obj.restore()
        except Record.DoesNotExist:
            return Response({"message": f"Jornal by ID - {journal} dose not exist!"}, status=404)
        return Response({"message": "Object restored successfully"}, status=200)


class JournalHistoryAPIView(ListAPIView, CreateAPIView):
    """
    API History Journal
    """
    permission_classes = (IsAuthenticated,)
    pagination_class = None

    def get(self, request, *args, **kwargs):
        journal_id = self.request.query_params.get('journal_id')
        indicator_values = RecordHistory.objects.filter(journal_document_id=journal_id).order_by("-created_at").first()
        serializer = JournalHistorySerializer(indicator_values)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        """
        POST запрос для создания истории журналов
        """
        journal = request.data.get("journal")
        stamp = request.data.get("stamp")
        author = request.user
        return journal_history_create(journal, author, stamp)


class DocumentFieldAPIViewOLD(ListAPIView):
    """
    API для полей документа
    """
    queryset = Indicator.objects.all()
    serializer_class = FieldSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        """
        GET запрос для получения полей по группе
        """
        q = self.queryset
        queryset = super(DocumentFieldAPIViewOLD, self).get_queryset()
        return queryset.filter(document=self.request.query_params["document"])


class FieldValueAPIViewOLD(ListAPIView, CreateAPIView, UpdateAPIView):
    queryset = RecordIndicatorValue.objects.all()
    serializer_class = FieldValueSerializer
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
        queryset = super(FieldValueAPIViewOLD, self).get_queryset()
        journal_id = self.request.query_params.get("journal_id")
        abc_document_id = self.request.query_params.get("abc_document_id")
        if abc_document_id:
            return queryset.filter(journal_document__abc_document_id=abc_document_id)
        return queryset.filter(journal_document__parent=journal_id)


class GetNotificationView(ListAPIView):
    """
    GET запрос для получения уведомлений
    """
    queryset = RecordIndicatorValue.objects.all()
    serializer_class = FieldValueSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        """
        GET запрос для получения выходных справочников по справочнику
        """
        queryset = super(GetNotificationView, self).get_queryset()
        user_id = self.request.query_params.get("user_id")
        user_code = self.request.query_params.get("user_code", 908)
        message_code = self.request.query_params.get("message_code", 902)
        users_idc_id = Indicator.objects.get(idc_code=user_code)
        message_idc_id = Indicator.objects.get(idc_code=message_code)
        value = queryset.filter(indicator_id=users_idc_id).values("indicator_value", "journal_document_id")
        idc_ids = []
        for val in value:
            if user_id in val["indicator_value"].split(","):
                idc_ids.append(val["journal_document_id"])
        return queryset.filter(indicator_id=message_idc_id, journal_document_id__in=idc_ids)


class DocumentationAPIVIew(TemplateView):
    template_name = 'documentation.html'
