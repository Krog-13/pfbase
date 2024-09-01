from dictionaries.models import Category, Indicator, \
    IndicatorParameter, ElementIndicatorValue, ABCDictionary, Element
from django.contrib import admin
from django import forms


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """
    Category in admin panel
    """
    list_display = ('short_name', 'parent', 'id')
    search_fields = ('short_name', 'parent__short_name', 'id')


class DictionaryAdminForm(forms.ModelForm):
    """
    Form for dictionaries in admin panel
    """
    full_name = forms.CharField(max_length=256, label='Полное наименование', required=True)
    part_name = forms.CharField(max_length=256, label='Краткое наименование', required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Check if the instance exists (editing an object)
        if self.instance.dct_name:
            self.fields['full_name'].initial = self.instance.dct_name.get("full_name", "")
            self.fields['part_name'].initial = self.instance.dct_name.get("short_name", "")


@admin.register(ABCDictionary)
class ABCDictionaryAdmin(admin.ModelAdmin):
    """
    Dictionary in admin panel
    """
    form = DictionaryAdminForm
    fields = (("full_name", "part_name"), "description", "code", "category", "author")
    list_display = ('get_short_name', 'author', 'code', 'id')
    search_fields = ('id', 'category__short_name')

    def get_short_name(self, obj):
        return obj.dct_name["short_name"]

    def save_model(self, request, obj, form, change):
        full_name = form.cleaned_data.get("full_name")
        part_name = form.cleaned_data.get("part_name")
        obj.full_name = full_name
        obj.part_name = part_name
        super().save_model(request, obj, form, change)


@admin.register(Indicator)
class IndicatorAdmin(admin.ModelAdmin):
    """
    Indicators in admin panel
    """
    fields = ("abc_dictionary", ("short_name", "type_value"), ("code", "index_sort"), "active", "reference", "parameters")
    list_display = ('get_short_name', 'type_value', 'abc_dictionary', 'index_sort')

    def get_short_name(self, obj):
        return obj.short_name.get("ru", obj.code)


@admin.register(Element)
class ElementAdmin(admin.ModelAdmin):
    """
    Elements in admin panel
    """
    fields = ("short_name", "abc_dictionary", "parent")
    list_display = ('get_short_name', 'abc_dictionary', 'id')
    search_fields = ('id',)

    def get_short_name(self, obj):
        return obj.short_name.get("ru")


@admin.register(IndicatorParameter)
class IndicatorParameterAdmin(admin.ModelAdmin):
    """
    Parameters in admin panel
    """
    list_display = ('short_name', 'active', 'id')
    search_fields = ('short_name', 'active', 'id')


@admin.register(ElementIndicatorValue)
class ElementIndicatorValueAdmin(admin.ModelAdmin):
    """
    Element-indicator values in admin panel
    """
    fields = (("value_str", "value_int"), "index_sort", "element", "indicator")
    list_display = ("value_int", "value_str", "element", "indicator")
    search_fields = ("value_int", "id")
