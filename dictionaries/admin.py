from dictionaries.models import Indicator, ElementIndicatorValue, ABCDictionary, Element
from django.contrib import admin
from django import forms


class DictionaryAdminForm(forms.ModelForm):
    """
    Form for dictionaries in admin panel
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


@admin.register(ABCDictionary)
class ABCDictionaryAdmin(admin.ModelAdmin):
    """
    Dictionary in admin panel
    """
    form = DictionaryAdminForm
    fields = (("ru_name", "en_name", "kz_name"), "description", "code", "active")
    list_display = ('get_name', 'author', 'code', 'id')

    def get_name(self, obj):
        return obj.name.get("ru", obj.code)

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
    list_display = ('get_short_name', 'abc_dictionary', 'id')
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
    list_display = ("value_int", "value_str", "element", "indicator")
    search_fields = ("value_int", "id")
