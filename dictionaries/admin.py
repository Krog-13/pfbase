from django.contrib import admin
from django import forms
from dictionaries.models import CategoryDictionary, DictionaryIndicator, \
    IndicatorParameter, DictionaryIndicatorValue, ABCDictionary, Element


@admin.register(CategoryDictionary)
class CategoryDictionaryAdmin(admin.ModelAdmin):
    """
    Категории справочников в админ панели
    """
    list_display = ('short_name', 'parent', 'id')
    search_fields = ('short_name', 'parent__short_name', 'id')


class DictionaryAdminForm(forms.ModelForm):
    """
    Форма для отчетов в админ панели
    """
    full_name = forms.CharField(max_length=256, label='Полное наименование', required=True)
    part_name = forms.CharField(max_length=256, label='Краткое наименование', required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Check if the instance exists (editing an object)
        if self.instance.naming:
            self.fields['full_name'].initial = self.instance.naming.get("full_name", "")
            self.fields['part_name'].initial = self.instance.naming.get("short_name", "")

    class Meta:
        model = Element
        fields = '__all__'


@admin.register(Element)
class DictionaryAdmin(admin.ModelAdmin):
    """
    Справочники в админ панели
    """
    fields = ("short_name", "code", "abc_dictionary", "parent")
    list_display = ('short_name', 'code', 'id')
    search_fields = ('id', 'code',
                     'category_dictionary__short_name',)


@admin.register(ABCDictionary)
class DictionaryAdmin(admin.ModelAdmin):
    """
    Dictionary in admin panel
    """
    form = DictionaryAdminForm
    fields = (("full_name", "part_name"), "description", "organizations", "abc_code", "category_dictionary", "author")
    list_display = ('get_short_name', 'author', 'abc_code', 'id')
    search_fields = ('id', 'category_dictionary__short_name')

    def get_short_name(self, obj):
        return obj.naming["short_name"]

    def save_model(self, request, obj, form, change):
        full_name = form.cleaned_data.get("full_name")
        part_name = form.cleaned_data.get("part_name")
        obj.full_name = full_name
        obj.part_name = part_name
        super().save_model(request, obj, form, change)


@admin.register(DictionaryIndicator)
class DictionaryIndicatorAdmin(admin.ModelAdmin):
    """
    Показатели в админ панели
    """
    fields = ("dictionary", ("short_name", "type_value"), "type_reference", "parameters")
    list_display = ('short_name', 'type_value', 'dictionary', 'id')
    search_fields = ('short_name', 'id')


@admin.register(IndicatorParameter)
class IndicatorParameterAdmin(admin.ModelAdmin):
    """
    Параметры в админ панели
    """
    list_display = ('short_name', 'id')
    search_fields = ('short_name', 'id')


@admin.register(DictionaryIndicatorValue)
class DictionaryIndicatorValueAdmin(admin.ModelAdmin):
    """
    Значения показателей в админ панели
    """
    # form = OrderForm
    list_display = ("indicator_value", "element", "indicator")
    search_fields = ("indicator_value", "id",
                     'dictionary__short_name')
