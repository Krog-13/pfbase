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
    fields = (("name", "description"), ("code", "index_sort"), "parent", "type")
    list_display = ("get_name", "code", "type", "parent", "id")
    list_select_related = ("parent",)
    search_fields = ('=id', "name")

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
    fields = (("status", "action"), "comment", "stamp", "sign_stamp", "record", "author")
    list_display = ('status', 'record', 'author', 'created_at', 'id')
    list_select_related = ("record", "author", "status", "record__document",)
    search_fields = ('=record__id', 'author__username', 'status__code',)
    readonly_fields = ("record",)
    list_per_page = 50


@admin.register(DcmIndicators)
class IndicatorAdmin(admin.ModelAdmin):
    """
    Indicator in the admin panel
    """
    fields = ("document", ("short_name", "full_name", "description"), "code", ("type_value", "type_extend"), "index_sort", "is_multiple", "is_required", "active")
    list_display = ("get_name", "code", "type_value", "document", "index_sort", "is_multiple", "is_required", "id")
    search_fields = ('=document__id', )
    list_filter = ("document",)
    list_per_page = 50

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
    fields = ("number", "date", "organization", "document", "parent", "active")
    list_display = ("number", "admin_document", "author", "parent", "id")
    list_select_related = ("author", "document", "parent")
    list_filter = ("document",)
    search_fields = ('=id', "number", '=document__id', "author__username",)
    autocomplete_fields = ("parent",)
    list_per_page = 50

    def save_model(self, request, obj, form, change):
        if not obj.pk:  # If the object is being created for the first time
            obj.author = request.user
        super().save_model(request, obj, form, change)


@admin.register(RecordIndicatorValues)
class RecordIndicatorValueAdmin(admin.ModelAdmin):
    """
    Record-Indicator Value in the admin panel
    """
    fieldsets = (
        (
            "Значения индикаторов", {
            "fields":
                [
                    "value_str",
                    ("value_int", "value_float"),
                    ("value_text", "value_json"),
                    ("value_array_int", "value_array_str"),
                    "value_datetime",
                    ("value_bool", "value_reference")
                ]
        }
        ),
        (
            "Other",
            {
                "fields": ["index_sort", "record", "indicator", "active"]
            }
        )
    )
    list_display = ("some_value", "type_value", "indicator", "record", "index_sort", "id")
    list_select_related = ("record", "indicator", "record__document",)
    search_fields = ('=record__id', 'indicator__short_name',)
    autocomplete_fields = ("record",)
    list_per_page = 50

    def type_value(self, obj):
        return obj.indicator.type_value

    type_value.admin_order_field = "indicator__type_value"

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
        elif obj.value_array_int:
            return "Array of int"
        elif obj.value_array_str:
            return "Array of str"
        elif obj.value_json:
            return "JSON data"
        else:
            return None

    def save_model(self, request, obj, form, change):
        if not obj.pk:  # If the object is being created for the first time
            obj.author = request.user
        super().save_model(request, obj, form, change)