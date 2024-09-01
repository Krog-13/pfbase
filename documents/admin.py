from .models import Category, IndicatorParameter, RecordIndicatorValue,\
    ABCDocument, Record, Indicator, RecordHistory
from dictionaries.models import ABCDictionary
from django.contrib import admin
from django import forms


@admin.register(Category)
class CategoryDocumentAdmin(admin.ModelAdmin):
    """
    Categories in the admin panel
    """
    list_display = ('short_name', 'parent', 'id')
    search_fields = ('short_name', 'parent__short_name', 'id')


class ABCDocumentAdminForm(forms.ModelForm):
    """
    Form for ABCDocument
    """
    full_name = forms.CharField(max_length=256, label='Полное наименование', required=True)
    part_name = forms.CharField(max_length=256, label='Краткое наименование', required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Check if the instance exists (editing an object)
        if self.instance.dcm_name:
            self.fields['full_name'].initial = self.instance.dcm_name.get("full_name", "")
            self.fields['part_name'].initial = self.instance.dcm_name.get("short_name", "")

    class Meta:
        model = ABCDocument
        fields = '__all__'


@admin.register(ABCDocument)
class ABCDocumentAdmin(admin.ModelAdmin):
    """
    Abstract Documents in the admin panel
    """
    form = ABCDocumentAdminForm
    fields = (("full_name", "part_name"), "description", "code", "category", "author")
    list_display = ("get_short_name", "code", "id")
    search_fields = ('get_short_name', 'id')

    def get_short_name(self, obj):
        return obj.dcm_name["short_name"]

    def save_model(self, request, obj, form, change):
        full_name = form.cleaned_data.get("full_name")
        part_name = form.cleaned_data.get("part_name")
        obj.full_name = full_name
        obj.part_name = part_name
        super().save_model(request, obj, form, change)


@admin.register(RecordHistory)
class RecordHistoryAdmin(admin.ModelAdmin):
    """
    Record History
    """
    list_display = ('status', 'status_comment', 'author')


@admin.register(IndicatorParameter)
class DefaultParameterAdmin(admin.ModelAdmin):
    """
    Parameters in admin panel
    """
    list_display = ('short_name', 'active', 'id')
    search_fields = ('short_name', 'active', 'id')


class IndicatorForm(forms.ModelForm):
    """
    Foreign Key
    """
    model_doc = ABCDocument.objects.all()
    model_dict = ABCDictionary.objects.all()
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


@admin.register(Indicator)
class IndicatorAdmin(admin.ModelAdmin):
    """
    Indicator in the admin panel
    """
    form = IndicatorForm
    exclude = ['reference']
    fields = ("abc_document", ("short_name", "type_value"), "parameters", "code", ("doc_fk", "dict_fk"), "custom_rule")
    list_display = ("get_short_name", "abc_document", "index_sort", "code", "id")
    search_fields = ('short_name', 'id')
    list_filter = ("abc_document",)

    def get_short_name(self, obj):
        return obj.short_name.get("ru", obj.code)

    def save_model(self, request, obj, form, change):
        document = form.cleaned_data.get("doc_fk")
        dictionary = form.cleaned_data.get("dict_fk")
        if document:
            obj.reference = document.abc_code  # or document.id
        elif dictionary:
            obj.reference = dictionary.abc_code  # or dictionary.id
        super().save_model(request, obj, form, change)


@admin.register(Record)
class RecordAdmin(admin.ModelAdmin):
    """
    Records in the admin panel
    """
    fields = ("short_name",
              "author", "abc_document", "parent")
    list_display = ('get_short_name', 'author', 'abc_document', 'id')
    list_filter = ("author",)

    def get_short_name(self, obj):
        return obj.short_name.get("ru")


@admin.register(RecordIndicatorValue)
class RecordIndicatorValueAdmin(admin.ModelAdmin):
    """
    Record-Indicator Value in the admin panel
    """
    fields = (("value_int", "value_str", "value_text"), "value_datetime", "value_reference",
              "index_sort", "record", "indicator")
    list_display = ("value_int", "value_str", "value_text", "value_datetime",
                    "value_reference", "record", "indicator", "index_sort")
    search_fields = (
        'field_value', 'output_document__document__short_name', 'id')
