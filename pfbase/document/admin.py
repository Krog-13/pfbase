from .models.documents import Documents
from .models.indicators import DcmIndicators
from .models.records import Records
from .models.rivalues import RecordIndicatorValues
from .models.rhistory import RecordHistory
from ..dictionary.models.dictionaries import Dictionaries
from django.contrib import admin
from django import forms


# Admin for Documents
@admin.register(Documents)
class DocumentAdmin(admin.ModelAdmin):
    """
    Abstract Documents in the admin panel
    """
    fields = ("name", "description", "code", "parent")
    list_display = ("get_name", "code", "parent", "id")
    search_fields = ('get_name', 'id')

    def get_name(self, obj):
        return obj.name["ru"]

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.author = request.user
        super().save_model(request, obj, form, change)


@admin.register(RecordHistory)
class RecordHistoryAdmin(admin.ModelAdmin):
    """
    Record History
    """
    list_display = ('status', 'status_comment', 'author')


class DcmIndicatorForm(forms.ModelForm):
    """
    Foreign Key
    """
    model_doc = Documents.objects.all()
    model_dict = Dictionaries.objects.all()
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


@admin.register(DcmIndicators)
class IndicatorAdmin(admin.ModelAdmin):
    """
    Indicator in the admin panel
    """
    form = DcmIndicatorForm
    exclude = ['reference']
    fields = ("document", ("name", "type_value", "type_extend"), "code",
              "active")
    list_display = ("get_name", "code", "type_value", "document", "index_sort", "id")
    search_fields = ('name', 'id')
    list_filter = ("document", "author")

    def get_name(self, obj):
        return obj.name.get("ru", obj.code)

    def save_model(self, request, obj, form, change):
        document = form.cleaned_data.get("doc_fk")
        dictionary = form.cleaned_data.get("dict_fk")
        if document:
            obj.reference = document.code  # or document.id
        elif dictionary:
            obj.reference = dictionary.code  # or dictionary.id
        if not obj.pk:
            obj.author = request.user
        super().save_model(request, obj, form, change)


@admin.register(Records)
class RecordAdmin(admin.ModelAdmin):
    """
    Records in the admin panel
    """
    fields = ("number", "date", "active", "document", "organization", "parent")
    list_display = ("number", "document", "author", "parent", "id")
    list_filter = ("document", "author")

    def save_model(self, request, obj, form, change):
        if not obj.pk:  # If the object is being created for the first time
            obj.author = request.user
        super().save_model(request, obj, form, change)


@admin.register(RecordIndicatorValues)
class RecordIndicatorValueAdmin(admin.ModelAdmin):
    """
    Record-Indicator Value in the admin panel
    """
    fields = (("value_int", "value_str", "value_text"), "value_datetime", "value_reference",
              "index_sort", "record", "indicator", "active")
    list_display = ("some_value", "type_value", "indicator", "record", "index_sort", "id")
    search_fields = (
        'field_value', 'output_document__document__short_name', 'id')
    list_filter = ("record",)

    def type_value(self, obj):
        return obj.indicator.type_value

    def some_value(self, obj):
        if obj.value_int:
            return obj.value_int
        elif obj.value_str:
            return obj.value_str
        elif obj.value_text:
            return obj.value_text
        elif obj.value_datetime:
            return obj.value_datetime
        elif obj.value_reference:
            return obj.value_reference
        elif obj.value_bool:
            return obj.value_bool
        else:
            return None

    def save_model(self, request, obj, form, change):
        if not obj.pk:  # If the object is being created for the first time
            obj.author = request.user
        super().save_model(request, obj, form, change)