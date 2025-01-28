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
    fields = ("name", "description", "code", "type", "index_sort", "parent")
    list_display = ("get_name", "code", "type", "parent", "index_sort", "id")
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
    list_display = ('status', 'record', 'author', 'created_at', 'id')


@admin.register(DcmIndicators)
class IndicatorAdmin(admin.ModelAdmin):
    """
    Indicator in the admin panel
    """
    fields = ("document", ("short_name", "full_name", "type_value", "type_extend"), "code",
              "active")
    list_display = ("get_name", "code", "type_value", "document", "index_sort", "id")
    search_fields = ('name', 'id')
    list_filter = ("document", "author")

    def get_name(self, obj):
        return obj.short_name.get("ru", obj.code)

    def save_model(self, request, obj, form, change):
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
    fields = (("value_int", "value_float", "value_str", "value_text", "value_json"), "value_datetime", "value_reference",
              "index_sort", "record", "indicator", "active")
    list_display = ("some_value", "type_value", "indicator", "record", "index_sort", "id")
    search_fields = (
        'field_value', 'id')
    list_filter = ("record",)

    def type_value(self, obj):
        return obj.indicator.type_value

    def some_value(self, obj):
        if obj.value_int:
            return obj.value_int
        elif obj.value_float:
            return obj.value_float
        elif obj.value_str:
            return obj.value_str
        elif obj.value_text:
            return obj.value_text[:10]
        elif obj.value_datetime:
            return obj.value_datetime
        elif obj.value_reference:
            return obj.value_reference
        elif obj.value_bool:
            return obj.value_bool
        elif obj.value_json:
            return "JSON data"
        else:
            return None

    def save_model(self, request, obj, form, change):
        if not obj.pk:  # If the object is being created for the first time
            obj.author = request.user
        super().save_model(request, obj, form, change)