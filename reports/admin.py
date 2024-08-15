from django.contrib import admin
from django import forms
from .models import HistoryReportJournal, CategoryReport, ABCReport, JournalReport, DefaultParameter, ReportIndicator,\
    IndicatorValue


@admin.register(HistoryReportJournal)
class HistoryJournalAdmin(admin.ModelAdmin):
    """
    История отчетов в админ панели
    """
    list_display = ('journal_status', 'author', 'journal_report')


@admin.register(CategoryReport)
class CategoryReportAdmin(admin.ModelAdmin):
    """
    Категорий Отчетов в админ панели
    """
    list_display = ('short_name', 'parent', 'id')
    search_fields = ('short_name', 'parent__short_name', 'id')


class ReportAdminForm(forms.ModelForm):
    """
    Форма для отчетов в админ панели
    """
    full_name = forms.CharField(max_length=256, label='Полное наименование', required=True)
    part_name = forms.CharField(max_length=256, label='Краткое наименование', required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Check if the instance exists (editing an object)
        if self.instance.naming:
            self.fields['full_name'].initial = self.instance.naming.get("full_name", "")
            self.fields['part_name'].initial = self.instance.naming.get("short_name", "")

    class Meta:
        model = ABCReport
        fields = '__all__'


class IndicatorForm(forms.ModelForm):
    """
    References
    """
    model_doc = ABCReport.objects.all()
    model_dict = ABCReport.objects.all()
    dict_fk = forms.ModelChoiceField(model_dict, label="Справочник", required=False)
    doc_fk = forms.ModelChoiceField(model_doc, label="Документ", required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Check if the instance exists (editing an object)
        if self.instance:
            if self.instance.type_value == "dcm":
                self.fields['doc_fk'].initial = self.instance.reference
            elif self.instance.type_value == "dct":
                self.fields['dict_fk'].initial = self.instance.reference


@admin.register(JournalReport)
class ReportAdmin(admin.ModelAdmin):
    """
    Справочники в админ панели
    """
    fields = ("short_name", "code", "period", "period_value", "rpt_number", "date_time",
              "author", "abc_report", "parent")
    list_display = ('short_name', 'code', 'id')
    search_fields = ('id', 'code')


@admin.register(ABCReport)
class DocumentAdmin(admin.ModelAdmin):
    """
    Документы в админ панели
    """
    form = ReportAdminForm
    fields = (("full_name", "part_name"), "description", "organizations", "category_report", "author")
    list_display = ("get_short_name", "id")
    search_fields = ('get_short_name', 'category_report__short_name', 'id')

    def get_short_name(self, obj):
        return obj.naming["short_name"]

    def save_model(self, request, obj, form, change):
        full_name = form.cleaned_data.get("full_name")
        part_name = form.cleaned_data.get("part_name")
        obj.full_name = full_name
        obj.part_name = part_name
        super().save_model(request, obj, form, change)


@admin.register(DefaultParameter)
class DefaultParameterAdmin(admin.ModelAdmin):
    """
    Параметры в админ панели
    """
    list_display = ('short_name', 'id')
    search_fields = ('short_name', 'id')


@admin.register(ReportIndicator)
class FieldAdmin(admin.ModelAdmin):
    """
    Поля в админ панели
    """
    form = IndicatorForm
    exclude = ['reference']
    fields = ("report", ("short_name", "type_value"), "parameters", ("doc_fk", "dict_fk"), "custom_rule")
    list_display = ("short_name", "id")
    search_fields = ('short_name', 'id')

    def save_model(self, request, obj, form, change):
        document = form.cleaned_data.get("doc_fk")
        dictionary = form.cleaned_data.get("dict_fk")
        if document:
            obj.reference = document.id
        elif dictionary:
            obj.reference = dictionary.id
        super().save_model(request, obj, form, change)


# @admin.register(IndicatorValue)
# class FieldValueAdmin(admin.ModelAdmin):
#     """
#     Значения полей в админ панели
#     """
#     list_display = ("indicator_value", "journal_report", "indicator")
