from rest_framework import serializers
from .models import JournalReport, HistoryReportJournal, ReportIndicator, IndicatorValue, CategoryReport, ABCReport,\
    DefaultParameter
from documents.models import JournalDocument


class CategoryReportSerializer(serializers.ModelSerializer):
    """
    Сериализатор для категорий отчетов
    """
    # children = serializers.SerializerMethodField()
    # reports = serializers.SerializerMethodField()

    class Meta:
        model = CategoryReport
        fields = ("id", "short_name", "description")
        # fields = ("id", "short_name", "description",
        #           "index_sort", "parent", "children", "reports")

    def get_children(self, obj):
        """
        Функция для проверки дочерних категорий
        """
        children_qs = obj.children.all()
        if children_qs.exists():
            return True
        return False

    def get_reports(self, obj):
        """
        Функция для проверки отчетов в категории
        """
        reports = JournalReport.objects.filter(category_report=obj.id)
        if reports.exists():
            return True
        return False


class ReportSerializer(serializers.ModelSerializer):
    """
    Сериализатор для журналов отчета
    """
    # children = serializers.SerializerMethodField()
    # status = serializers.SerializerMethodField()

    class Meta:
        model = JournalReport
        fields = ("id", "code", "abc_report", "parent", "status",
                  "rpt_number", "date_time")

    def get_status(self, obj):
        last_status = obj.history_status.last()
        if last_status:
            return JournalHistorySerializer(last_status).data

    def get_children(self, obj):
        """
        Функция для проверки дочерних категорий
        """
        children_qs = obj.children.all()
        if children_qs.exists():
            return True
        return False

class FieldValue2Serializer(serializers.ModelSerializer):
    """
    Сериализатор для значений полей
    """
    indicator = serializers.SerializerMethodField()

    class Meta:
        model = IndicatorValue
        fields = ("indicator",)

    def get_indicator(self, obj):
        result = []
        for i in obj:
            indicator = ReportIndicator.objects.get(id=i.indicator_id)
            if indicator.type_value == "dct":
                element = JournalDocument.objects.get(id=i.indicator_value)
                short_name = element.short_name
                code = element.abc_dictionary.abc_code
            else:
                short_name = i.indicator_value
                code = indicator.idc_code
            idc = {"id": i.id, "value": short_name, "label": i.indicator.short_name,
                   "type": i.indicator.type_value, "code": code}
            result.append(idc)
        return result


class JournalDetailSerializer(serializers.ModelSerializer):
    """
    Сериализатор для Elements
    """
    children = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    indicator_value = serializers.SerializerMethodField()

    class Meta:
        model = JournalReport
        fields = ("id", "short_name", "code", "abc_report", "parent", "children",
                  "doc_number", "date_time", "status", "indicator_value")

    def get_indicator_value(self, obj):
        indicators = obj.journal_doc.all()
        return FieldValue2Serializer(indicators).data

    def get_status(self, obj):
        last_status = obj.history_status.last()
        if last_status:
            return JournalHistorySerializer(last_status).data

    def get_children(self, obj):
        """
        Функция для проверки дочерних категорий
        """
        children_qs = obj.children.all()
        if children_qs.exists():
            return True
        return False

class DocumentSerializer(serializers.ModelSerializer):
    """
    Сериализатор для документов
    """
    class Meta:
        model = ABCReport
        fields = ("id", "naming", "description", "category_document")

class JournalHistorySerializer(serializers.ModelSerializer):
    """
    Serialize
    """
    author = serializers.CharField(source="author.get_full_name")

    class Meta:
        model = HistoryReportJournal
        fields = ("journal_status", "status_comment", "created_at", "author")


class IndicatorSerializer(serializers.ModelSerializer):
    parameters = serializers.SlugRelatedField(
        slug_field="short_name", queryset=DefaultParameter.objects.all(), many=True)

    class Meta:
        model = ReportIndicator
        fields = ("id", "short_name", "type_value", "parameters", "reference")


class IndicatorValueSerializer(serializers.ModelSerializer):
    """
    Сериализатор для значений показателей
    """

    indicator_info = serializers.SerializerMethodField()
    indicator = serializers.SerializerMethodField()

    class Meta:
        model = IndicatorValue
        fields = ("indicator", "indicator_info", )

    def get_indicator(self, obj):
        short_name = JournalReport.objects.values("short_name").get(id=obj.indicator_value)
        return short_name

    def get_indicator_info(self, obj):
        if obj.indicator:
            indicator = obj.indicator
            return {"short_name": indicator.short_name, "type_value": indicator.type_value}
