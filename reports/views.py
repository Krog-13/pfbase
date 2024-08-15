from rest_framework.generics import ListAPIView, UpdateAPIView, CreateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from .models import IndicatorValue, CategoryReport, JournalReport, HistoryReportJournal, ABCReport, ReportIndicator
from .serializers import ReportSerializer, IndicatorSerializer, JournalDetailSerializer, \
    JournalHistorySerializer, IndicatorValueSerializer, CategoryReportSerializer
from .common import journal_history_create, journal_create
from rest_framework.pagination import PageNumberPagination


class CustomPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class GIndicatorAPIView(ModelViewSet):
    """
    API для группы показателей
    """
    queryset = CategoryReport.objects.all()
    serializer_class = CategoryReportSerializer

    def get(self, request, *args, **kwargs):
        return Response({"message": "Hello, world!"})

    # def get_queryset(self):
    #     """
    #     GET запрос для получения группы показателей
    #     """
    #     queryset = super(GIndicatorAPIView, self).get_queryset()
    #     if self.request.query_params.get("report"):
    #         return queryset.filter(report=self.request.query_params["report"])
    #     return queryset



class CategoryReportAPIView(ListAPIView):
    """
    API для категорий отчетов
    """
    queryset = CategoryReport.objects.filter(parent__isnull=True)
    serializer_class = CategoryReportSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        """
        GET запрос для получения категорий отчетов
        """
        parent_id = self.request.query_params.get("parent_id")
        return CategoryReport.objects.filter(parent_id=parent_id)


class JournalReportAPIView(ListAPIView, CreateAPIView, UpdateAPIView):
    """
    API для отчетов
    """
    queryset = JournalReport.objects.all().order_by("id")
    serializer_class = ReportSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = CustomPagination

    def get_queryset(self):
        """
        GET запрос для получения отчетов
        """
        report_id = self.request.user.organization_id  # organization pass

        report = self.request.query_params.get('report_id')
        parent = self.request.query_params.get('parent_id')
        journal = self.request.query_params.get('journal_id')
        queryset = super(JournalReportAPIView, self).get_queryset()
        if report:
            return queryset.filter(abc_document=report, parent=parent)
        elif journal:
            return queryset.filter(id=journal)
        else:
            return queryset.all()

    def create(self, request, *args, **kwargs):
        """
        POST запрос для создания значений показателей
        """
        element = request.data.get("journal")
        indicator_value = request.data.get("indicator")
        user = request.user
        try:
            return journal_create(element, indicator_value, user)
        except IndexError:
            return Response({"Msg": "Something wrong please correction your query!"},
                     status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        """
        Delete
        """
        journal = self.request.query_params.get('journal_id')
        try:
            obj = JournalReport.objects.get(id=journal)
            obj.soft_delete()
        except JournalReport.DoesNotExist:
            return Response({"message": f"Jornal by ID - {journal} dose not exist!"}, status=404)
        return Response({"message": "Object deleted successfully"}, status=204)

    def update(self, request, *args, **kwargs):
        """Restore object"""
        journal = self.request.query_params.get('journal_id')
        try:
            obj = JournalReport.everything.get(id=journal)
            obj.restore()
        except JournalReport.DoesNotExist:
            return Response({"message": f"Jornal by ID - {journal} dose not exist!"}, status=404)
        return Response({"message": "Object restored successfully"}, status=200)


class JournalDetailAPIView(ListAPIView):
    """"""
    queryset = JournalReport.objects.all()
    serializer_class = JournalDetailSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        journal = self.request.query_params.get('journal_id')
        queryset = super(JournalDetailAPIView, self).get_queryset()
        return queryset.filter(id=journal)


class JournalHistoryAPIView(ListAPIView, CreateAPIView):
    """
    API History Journal
    """
    permission_classes = (IsAuthenticated,)
    pagination_class = None

    def get(self, request, *args, **kwargs):
        journal_id = self.request.query_params.get('journal_id')
        indicator_values = HistoryReportJournal.objects.filter(journal_document_id=journal_id).order_by("-created_at").first()
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


class ReportIndicatorAPIView(ListAPIView):
    """
    API для показателей
    """
    queryset = ReportIndicator.objects.all()
    serializer_class = IndicatorSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        """
        GET запрос для получения полей по группе
        """
        queryset = super(ReportIndicatorAPIView, self).get_queryset()
        return queryset.filter(document=self.request.query_params["document"])


class IndicatorValueAPIView(ListAPIView, CreateAPIView, UpdateAPIView):
    """
    API для значений показателей
    """
    queryset = IndicatorValue.objects.all()
    serializer_class = IndicatorValueSerializer
    permission_classes = (IsAuthenticated,)

    def create(self, request, *args, **kwargs):
        """
        POST запрос для создания значений показателей
        """
        pass

    def get_queryset(self):
        """
        GET запрос для получения выходных справочников по справочнику
        """
        queryset = super(IndicatorValueAPIView, self).get_queryset()
        journal_id = self.request.query_params.get("journal_id")
        return queryset.filter(journal_document_id=journal_id)


class ReportAPIView(ListAPIView):
    """
    API для документов
    """
    queryset = ABCReport.objects.all()
    serializer_class = ReportSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        """
        GET запрос для получения документов по категории
        """
        document_id = self.request.user.organization_id
        category_id = self.request.query_params.get('category_id')
        if category_id:
            queryset = super(ReportAPIView, self).get_queryset()
            return queryset.filter(category_document__id=category_id, organizations=document_id)
        else:
            queryset = super(ReportAPIView, self).get_queryset()
            return queryset.filter(organizations=document_id)
