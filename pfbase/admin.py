"""
Main admin by Pertro Flow project
"""
from django.contrib import admin
from django import forms
from .models import RecordIndicatorValue, ABCDocument, Record, DcmIndicator, RecordHistory,\
    Element, ABCDictionary, DctIndicator, ElementIndicatorValue, ElementHistory, PFEnum, Notification


# Admin for Dictionaries
@admin.register(ABCDictionary)
class ABCDictionaryAdmin(admin.ModelAdmin):
    """
    Dictionary in admin panel
    """
    fields = ("name", "description", "code", "active")
    list_display = ('get_name', 'author', 'code', 'id')

    def get_name(self, obj):
        return obj.name.get("ru", obj.code)

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.author = request.user
        super().save_model(request, obj, form, change)


@admin.register(DctIndicator)
class DctIndicatorAdmin(admin.ModelAdmin):
    """
    Indicators in admin panel
    """
    fields = ("abc_dictionary", ("name", "type_value", "type_extend"), "description", ("code", "index_sort"), "active", "reference")
    list_display = ('get_name', 'type_value', 'abc_dictionary', 'index_sort')

    def get_name(self, obj):
        return obj.name.get("ru", obj.code)

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.author = request.user
        super().save_model(request, obj, form, change)


@admin.register(Element)
class ElementAdmin(admin.ModelAdmin):
    """
    Elements in admin panel
    """
    fields = ("short_name", "full_name", "abc_dictionary", "code", "parent", "active")
    list_display = ('get_short_name', 'abc_dictionary', "code", 'id')
    search_fields = ('id',)

    def get_short_name(self, obj):
        return obj.short_name.get("ru")

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.author = request.user
        super().save_model(request, obj, form, change)


@admin.register(ElementIndicatorValue)
class ElementIndicatorValueAdmin(admin.ModelAdmin):
    """
    Element-indicator values in admin panel
    """
    fields = (("value_str", "value_int", "value_text", "value_datetime", "value_reference"),
              "index_sort", "element", "indicator")
    list_display = ("value_int", "value_str", "value_datetime", "value_reference", "element", "indicator")
    search_fields = ("value_int", "id")


@admin.register(ElementHistory)
class ElementHistoryAdmin(admin.ModelAdmin):
    """
    Element history in admin panel
    """
    search_fields = ("element", "id")


# Admin for Documents
@admin.register(ABCDocument)
class ABCDocumentAdmin(admin.ModelAdmin):
    """
    Abstract Documents in the admin panel
    """
    fields = ("name", "description", "code")
    list_display = ("get_name", "code", "id")
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


@admin.register(DcmIndicator)
class IndicatorAdmin(admin.ModelAdmin):
    """
    Indicator in the admin panel
    """
    form = DcmIndicatorForm
    exclude = ['reference']
    fields = ("abc_document", ("name", "type_value", "type_extend"), "code",
              "active")
    list_display = ("get_name", "abc_document", "index_sort", "code", "id")
    search_fields = ('name', 'id')
    list_filter = ("abc_document",)

    def get_name(self, obj):
        return obj.name.get("ru", obj.code)

    def save_model(self, request, obj, form, change):
        document = form.cleaned_data.get("doc_fk")
        dictionary = form.cleaned_data.get("dict_fk")
        if document:
            obj.reference = document.abc_code  # or document.id
        elif dictionary:
            obj.reference = dictionary.abc_code  # or dictionary.id
        if not obj.pk:
            obj.author = request.user
        super().save_model(request, obj, form, change)


@admin.register(Record)
class RecordAdmin(admin.ModelAdmin):
    """
    Records in the admin panel
    """
    fields = ("number", "date", "active", "abc_document", "parent")
    list_display = ('number', 'author', 'abc_document', 'id')
    list_filter = ("author",)

    def save_model(self, request, obj, form, change):
        if not obj.pk:  # If the object is being created for the first time
            obj.author = request.user
        super().save_model(request, obj, form, change)


@admin.register(RecordIndicatorValue)
class RecordIndicatorValueAdmin(admin.ModelAdmin):
    """
    Record-Indicator Value in the admin panel
    """
    fields = (("value_int", "value_str", "value_text"), "value_datetime", "value_reference",
              "index_sort", "record", "indicator", "active")
    list_display = ("value_int", "value_str", "value_text", "value_datetime",
                    "value_reference", "record", "indicator", "index_sort")
    search_fields = (
        'field_value', 'output_document__document__short_name', 'id')

    def save_model(self, request, obj, form, change):
        if not obj.pk:  # If the object is being created for the first time
            obj.author = request.user
        super().save_model(request, obj, form, change)


# Admin for System
@admin.register(PFEnum)
class PFEnumAdmin(admin.ModelAdmin):
    """
    Enum in admin panel
    """
    list_display = ('list', 'code', 'id')

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.author = request.user
        super().save_model(request, obj, form, change)


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """
    Notification in admin panel
    """
    list_display = ('type_notification', 'source_user', 'user', 'id')
