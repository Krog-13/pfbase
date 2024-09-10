from dictionaries.models import Indicator, ElementIndicatorValue, ABCDictionary, Element, ElementHistory
from django.contrib import admin


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


@admin.register(Indicator)
class IndicatorAdmin(admin.ModelAdmin):
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
