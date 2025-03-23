from pfbase.document.models.business import *
from pfbase.dictionary.models import *
from pfbase.business_values_fields import INDICATOR_TO_VALUE_FIELD, MAPPING


def get_target_field(indicator):
    if indicator.is_multiple:
        if indicator.type_value in INDICATOR_FOR_MULTIPLE_STR_UPLOAD:
            return 'value_array_str'
        elif indicator.type_value in INDICATOR_FOR_MULTIPLE_INT_UPLOAD:
            return 'value_array_int'
        else:
            return INDICATOR_TO_VALUE_FIELD.get(indicator.type_value, 'value_str')
    else:
        return INDICATOR_TO_VALUE_FIELD.get(indicator.type_value, 'value_str')


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

    def create(self, **kwargs):
        element_fields = {}
        for field in ['active', 'parent', 'author', 'organization']:
            if field in kwargs:
                element_fields[field] = kwargs.pop(field)
        element_fields['dictionary'] = self.dictionary
        element = Elements.objects.create(**element_fields)
        for indicator in self.dictionary.indicators.all():
            if indicator.code in kwargs:
                value = kwargs[indicator.code]
                target_field = get_target_field(indicator)
                if indicator.is_multiple and indicator.type_value in INDICATOR_FOR_MULTIPLE_STR_UPLOAD:
                    value = value.split(';')
                indicator_value_data = {
                    'element': element,
                    'indicator': indicator,
                    target_field: value
                }
                ElementIndicatorValues.objects.create(**indicator_value_data)
        return element

    def update_instance(self, instance, **kwargs):
        element_fields = ['active', 'parent', 'author', 'organization']
        for field in element_fields:
            if field in kwargs:
                setattr(instance, field, kwargs.pop(field))
        instance.save()
        for indicator in self.dictionary.indicators.all():
            if indicator.code in kwargs:
                value = kwargs[indicator.code]
                target_field = get_target_field(indicator)

                try:
                    indicator_value = ElementIndicatorValues.objects.get(element=instance, indicator=indicator)
                    setattr(indicator_value, target_field, value)
                    indicator_value.save()
                except ElementIndicatorValues.DoesNotExist:
                    ElementIndicatorValues.objects.create(
                        element=instance,
                        indicator=indicator,
                        **{target_field: value},
                    )
        return instance

    def delete_instance(self, instance):
        ElementIndicatorValues.objects.filter(element=instance).delete()
        instance.delete()


def get_field_class_for_indicator(indicator):
    field_class = MAPPING.get(indicator.type_value)
    if not field_class:
        raise Exception(f"Тип индикатора {indicator.type_value} не поддерживается")
    return field_class


_BUSINESS_DICTIONARY_MODEL_CACHE = {}


def BusinessDictionaryModel(dictionary_code):
    if dictionary_code in _BUSINESS_DICTIONARY_MODEL_CACHE:
        return _BUSINESS_DICTIONARY_MODEL_CACHE[dictionary_code]
    try:
        dictionary = Dictionaries.objects.get(code=dictionary_code)
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
    business_model = type(model_name, (models.Model,), dynamic_fields)
    _BUSINESS_DICTIONARY_MODEL_CACHE[dictionary_code] = business_model
    return business_model
