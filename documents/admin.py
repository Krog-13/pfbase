from .models import RecordIndicatorValue,\
    ABCDocument, Record, Indicator, RecordHistory
from dictionaries.models import ABCDictionary
from django.contrib import admin
from django import forms


class ABCDocumentAdminForm(forms.ModelForm):
    """
    Form for ABCDocument
    """
    ru_name = forms.CharField(max_length=256, label='RU наименование', required=True)
    en_name = forms.CharField(max_length=256, label='EN наименование', required=False)
    kz_name = forms.CharField(max_length=256, label='KZ наименование', required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Check if the instance exists (editing an object)
        if self.instance.name:
            self.fields['ru_name'].initial = self.instance.name.get("ru", "")
            self.fields['en_name'].initial = self.instance.name.get("en", "")
            self.fields['kz_name'].initial = self.instance.name.get("kz", "")

    class Meta:
        model = ABCDocument
        fields = '__all__'


@admin.register(ABCDocument)
class ABCDocumentAdmin(admin.ModelAdmin):
    """
    Abstract Documents in the admin panel
    """
    form = ABCDocumentAdminForm
    fields = (("ru_name", "en_name", "kz_name"), "description", "code", "author")
    list_display = ("get_name", "code", "id")
    search_fields = ('get_name', 'id')

    def get_name(self, obj):
        return obj.name["ru"]

    def save_model(self, request, obj, form, change):
        ru_name = form.cleaned_data.get("ru_name")
        en_name = form.cleaned_data.get("en_name")
        kz_name = form.cleaned_data.get("kz_name")
        obj.ru_name = ru_name
        obj.en_name = en_name
        obj.kz_name = kz_name
        if not obj.pk:
            obj.author = request.user
        super().save_model(request, obj, form, change)


@admin.register(RecordHistory)
class RecordHistoryAdmin(admin.ModelAdmin):
    """
    Record History
    """
    list_display = ('status', 'status_comment', 'author')


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
    fields = ("abc_document", ("name", "type_value", "type_extend"), "code",
              "active", "author")
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
    fields = ("number", "date", "active",
              "author", "abc_document", "parent")
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
              "index_sort", "record", "indicator", "active", "author")
    list_display = ("value_int", "value_str", "value_text", "value_datetime",
                    "value_reference", "record", "indicator", "index_sort")
    search_fields = (
        'field_value', 'output_document__document__short_name', 'id')
