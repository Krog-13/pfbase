from pfbase.document.models.dynamic_doc import *
from pfbase.dictionary.models import *
from pfbase.business_values_fields import INDICATOR_TO_VALUE_FIELD, MAPPING


class BusinessDictionaryElementsManager(models.Manager):
    def __init__(self, dictionary, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dictionary = dictionary

    def get_queryset(self):
        indicators = list(self.dictionary.indicators.all())
        qs = Elements.objects.filter(dictionary=self.dictionary)
        annotations = {}
        for indicator in indicators:
            value_field = INDICATOR_TO_VALUE_FIELD.get(indicator.type_value, 'value_str')
            subquery = ElementIndicatorValues.objects.filter(
                element=OuterRef('pk'),
                indicator=indicator,
            ).values(value_field)[:1]
            annotations[indicator.code] = Subquery(subquery)
        return qs.annotate(**annotations)


def get_field_class_for_indicator(indicator):
    field_class = MAPPING.get(indicator.type_value)
    if not field_class:
        raise Exception(f"Тип индикатора {indicator.type_value} не поддерживается")
    return field_class


_business_model_cache = {}


def BusinessDictionaryModel(dictionary_code):
    if dictionary_code in _business_model_cache:
        return _business_model_cache[dictionary_code]
    try:
        dictionary = Dictionaries.objects.get(id=dictionary_code)
    except ObjectDoesNotExist:
        raise ValueError(f"Справочник с кодом '{dictionary_code}' не найден")

    dynamic_fields = {
        'id': models.AutoField(primary_key=True),
        'short_name': models.JSONField(verbose_name="Краткое наименование", null=True),
        'full_name': models.JSONField(verbose_name="Полное наименование", null=True),
        'code': models.CharField(max_length=128, verbose_name="Код", null=True, blank=True),
        'active': models.BooleanField(default=True, verbose_name="Активный"),
    }

    for indicator in dictionary.indicators.all():
        field_class = get_field_class_for_indicator(indicator)
        field_kwargs = {
            'null': True,
            'blank': True,
            'verbose_name': indicator.short_name.get("ru", indicator.code)
        }
        if field_class == models.CharField:
            field_kwargs.setdefault('max_length', 255)
        dynamic_fields[indicator.code] = field_class(**field_kwargs)

    dynamic_fields['objects'] = BusinessDictionaryElementsManager(dictionary)
    dynamic_fields['__module__'] = __name__

    class Meta:
        managed = False
        db_table = dictionary.code

    dynamic_fields['Meta'] = Meta

    model_name = f"{dictionary.code.capitalize()}_BusinessModel"
    dynamic_model = type(model_name, (models.Model,), dynamic_fields)
    _business_model_cache[dictionary_code] = dynamic_model
    return dynamic_model
