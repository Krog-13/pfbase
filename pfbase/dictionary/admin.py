from .models.dictionaries import Dictionaries
from .models.indicators import DctIndicators
from .models.elements import Elements
from .models.eivalues import ElementIndicatorValues
from .models.ehistory import ElementHistory
from django.contrib import admin


# Admin for Dictionaries
@admin.register(Dictionaries)
class DictionaryAdmin(admin.ModelAdmin):
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


@admin.register(DctIndicators)
class IndicatorAdmin(admin.ModelAdmin):
    """
    Indicators in admin panel
    """
    fields = ("dictionary", ("name", "type_value", "type_extend"), "description", ("code", "index_sort"), "active", "reference")
    list_display = ("get_name", "code", "type_value", "dictionary", "index_sort", "id")
    list_filter = ("dictionary", "author")

    def get_name(self, obj):
        return obj.name.get("ru", obj.code)

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.author = request.user
        super().save_model(request, obj, form, change)


@admin.register(Elements)
class ElementAdmin(admin.ModelAdmin):
    """
    Elements in admin panel
    """
    fields = ("short_name", "full_name", "dictionary", "organization", "code", "parent", "active")
    list_display = ('get_short_name', 'dictionary', "code", "parent", 'id')
    list_filter = ("dictionary", "author")

    search_fields = ('id',)

    def get_short_name(self, obj):
        return obj.short_name.get("ru")

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.author = request.user
        super().save_model(request, obj, form, change)


@admin.register(ElementIndicatorValues)
class EIValueAdmin(admin.ModelAdmin):
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
