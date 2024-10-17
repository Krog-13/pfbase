"""
Main admin by Pertro Flow project
"""
from django.contrib import admin
from django import forms
from .models import RecordIndicatorValue, ABCDocument, Record, DcmIndicator, RecordHistory,\
    Element, ABCDictionary, DctIndicator, ElementIndicatorValue, ElementHistory, PFEnum,\
    Notification, Organization, User


# Admin for Dictionaries
@admin.register(ABCDictionary)
class ABCDictionaryAdmin(admin.ModelAdmin):
    """
    Dictionary in admin panel
    """
    fields = ("name", "description", "code", "active", "parent")
    list_display = ('get_name', 'author', 'code', 'parent', 'id')

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
    list_display = ("get_name", "code", "type_value", "abc_dictionary", "index_sort", "id")
    list_filter = ("abc_dictionary", "author")

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
    fields = ("short_name", "full_name", "abc_dictionary", "organization", "code", "parent", "active")
    list_display = ('get_short_name', 'abc_dictionary', "code", "parent", 'id')
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
    list_display = ("some_value", "type_value", "indicator", "element", "index_sort", "id")
    search_fields = ("value_int", "id")
    list_filter = ("element",)

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
    list_display = ("get_name", "code", "type_value", "abc_document", "index_sort", "id")
    search_fields = ('name', 'id')
    list_filter = ("abc_document", "author")

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
    fields = ("number", "date", "active", "abc_document", "organization", "parent")
    list_display = ("number", "abc_document", "author", "parent", "id")
    list_filter = ("abc_document", "author")

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


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    """
    Organization in admin panel
    """
    list_display = ('name', 'identifier', 'address', 'id')


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """
    User in admin panel
    """
    list_display = ('username', 'email', 'organization', 'id')


def get_app_list(self, request, app_label=None):
    """
    Return a sorted list of all the installed apps that have been
    registered in this site.
    """
    sort_apps = ['pfbase'] # add new app name for sorting if needed
    ordering = {  # add new model name if new app in sort_apps was added 
        "DCM Документы": 1,
        "DCM Индикаторы": 2,
        "DCM Записи документов": 3,
        "DCM Значения индикаторов": 4,
        "DCM Истории записей": 5,
        "DCT Справочники": 6,
        "DCT Индикаторы": 7,
        "DCT Элементы": 8,
        "DCT Значение индикаторов": 9,
        "DCT История элементов": 10,
        "SYS Перечисления": 11,
        "SYS Уведомления": 12,
        "SYS Организации": 13,
        "SYS Пользователи": 14,
    }
    app_dict = self._build_app_dict(request, app_label)
    app_list = sorted(app_dict.values(), key=lambda x: x['name'].lower())

    for app in app_list:
        if app['app_label'] in sort_apps: 
            app['models'].sort(key=lambda x: ordering[x['name']])

    # Sort so pfbase app always will be at the first place
    app_list.sort(key=lambda x: 0 if x['app_label'] == 'pfbase' else 1)
    return app_list

# Override get_app_list method in AdminSite
admin.AdminSite.get_app_list = get_app_list
