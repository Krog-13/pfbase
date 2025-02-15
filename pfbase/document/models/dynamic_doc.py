from django.db.models import Subquery, OuterRef
from django.core.exceptions import ImproperlyConfigured, ObjectDoesNotExist
from pfbase.document.models.rivalues import *
from pfbase.document.models.indicators import *


class IndicatorType(models.TextChoices):
    STRING = 'str', 'String'
    INTEGER = 'int', 'Integer'
    FLOAT = 'float', 'Float'
    BOOLEAN = 'bool', 'Boolean'
    LIST = 'list', 'List'
    DATETIME = 'datetime', 'Datetime'
    DATE = 'date', 'Date'
    TIME = 'time', 'Time'
    TEXT = 'text', 'Text'
    FILE = 'file', 'File'
    JSON = 'json', 'Json'
    DICTIONARY = 'dct', 'Dictionary'
    DOCUMENT = 'dcm', 'Document'
    CALCULATE = 'calc', 'Calculate'
    USER = 'user', 'User'
    ORGANIZATION = 'org', 'Organization'


def get_field_class_for_indicator(indicator):
    mapping = {
        IndicatorType.STRING: models.CharField,
        IndicatorType.TEXT: models.TextField,
        IndicatorType.INTEGER: models.IntegerField,
        IndicatorType.FLOAT: models.FloatField,
        IndicatorType.BOOLEAN: models.BooleanField,
        IndicatorType.DATETIME: models.DateTimeField,
        IndicatorType.DATE: models.DateTimeField,
        IndicatorType.TIME: models.DateTimeField,
        IndicatorType.JSON: models.JSONField,
        IndicatorType.FILE: models.CharField,
        IndicatorType.LIST: models.JSONField,
        IndicatorType.DICTIONARY: models.JSONField,
        IndicatorType.DOCUMENT: models.PositiveBigIntegerField,
        IndicatorType.CALCULATE: models.CharField,
        IndicatorType.USER: models.PositiveBigIntegerField,
        IndicatorType.ORGANIZATION: models.PositiveBigIntegerField,
    }
    field_class = mapping.get(indicator.type_value)
    if not field_class:
        raise ImproperlyConfigured(f"Тип индикатора {indicator.type_value} не поддерживается")
    return field_class

INDICATOR_TO_VALUE_FIELD = {
    IndicatorType.STRING: 'value_str',
    IndicatorType.TEXT: 'value_text',
    IndicatorType.INTEGER: 'value_int',
    IndicatorType.FLOAT: 'value_float',
    IndicatorType.BOOLEAN: 'value_bool',
    IndicatorType.DATETIME: 'value_datetime',
    IndicatorType.DATE: 'value_datetime',
    IndicatorType.TIME: 'value_datetime',
    IndicatorType.JSON: 'value_json',
    IndicatorType.FILE: 'value_str',
    IndicatorType.LIST: 'value_reference',
    IndicatorType.DICTIONARY: 'value_reference',
    IndicatorType.DOCUMENT: 'value_reference',
    IndicatorType.CALCULATE: 'value_str',
    IndicatorType.USER: 'value_reference',
    IndicatorType.ORGANIZATION: 'value_reference',
}


class DynamicModelManager(models.Manager):
    def __init__(self, document, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.document = document

    def get_queryset(self):
        qs = Records.objects.filter(document=self.document)

        for indicator in self.document.indicators.all():
            value_field = INDICATOR_TO_VALUE_FIELD.get(indicator.type_value, 'value_str')
            subquery = RecordIndicatorValues.objects.filter(
                record=OuterRef('pk'),
                indicator=indicator,
            ).values(value_field)[:1]
            qs = qs.annotate(**{indicator.code: Subquery(subquery)})
        return qs

    def create(self, **kwargs):
        record_fields = {}
        for field in ['number', 'date', 'active', 'parent', 'author', 'organization']:
            if field in kwargs:
                record_fields[field] = kwargs.pop(field)
        record_fields['document'] = self.document

        record = Records.objects.create(**record_fields)

        for indicator in self.document.indicators.all():
            if indicator.code in kwargs:
                value = kwargs[indicator.code]
                target_field = INDICATOR_TO_VALUE_FIELD.get(indicator.type_value, 'value_str')
                indicator_value_data = {
                    'record': record,
                    'indicator': indicator,
                    target_field: value
                }
                RecordIndicatorValues.objects.create(**indicator_value_data)
        return record

    def update_instance(self, instance, **kwargs):
        record_fields = ['number', 'date', 'active', 'parent', 'author', 'organization']
        for field in record_fields:
            if field in kwargs:
                setattr(instance, field, kwargs.pop(field))
        instance.save()

        for indicator in self.document.indicators.all():
            if indicator.code in kwargs:
                value = kwargs[indicator.code]
                target_field = INDICATOR_TO_VALUE_FIELD.get(indicator.type_value, 'value_str')
                try:
                    indicator_value = RecordIndicatorValues.objects.get(record=instance, indicator=indicator)
                    setattr(indicator_value, target_field, value)
                    indicator_value.save()
                except RecordIndicatorValues.DoesNotExist:
                    RecordIndicatorValues.objects.create(
                        record=instance,
                        indicator=indicator,
                        **{target_field: value}
                    )
        return instance

    def delete_instance(self, instance):
        RecordIndicatorValues.objects.filter(record=instance).delete()
        instance.delete()


def DynamicModel(document_code):
    try:
        document = Documents.objects.get(code=document_code)
    except ObjectDoesNotExist:
        raise ValueError(f"Документ с кодом '{document_code}' не найден")

    # Добавляем базовые поля, включая поля ForeignKey, чтобы они стали доступны в сериалайзере
    dynamic_fields = {
        'id': models.AutoField(primary_key=True),
        'number': models.CharField(max_length=255, verbose_name="Номер", null=True),
        'date': models.DateTimeField(verbose_name="Дата", null=True),
        'active': models.BooleanField(default=True, verbose_name="Активный"),
        # Добавляем поля, которые есть в модели Records
        'parent': models.ForeignKey('self', null=True, blank=True, related_name="children", on_delete=models.CASCADE, verbose_name='Родительская запись'),
        'author': models.ForeignKey("User", on_delete=models.CASCADE, verbose_name='Автор'),
        'organization': models.ForeignKey("Organization", on_delete=models.SET_NULL, blank=True, null=True, verbose_name='Организация'),
    }

    # Добавляем динамические поля на основе индикаторов
    for indicator in document.indicators.all():
        field_class = get_field_class_for_indicator(indicator)
        field_kwargs = {'null': True, 'blank': True, 'verbose_name': indicator.short_name.get("ru", indicator.code)}
        if field_class == models.CharField:
            field_kwargs.setdefault('max_length', 255)
        dynamic_fields[indicator.code] = field_class(**field_kwargs)

    dynamic_fields['objects'] = DynamicModelManager(document)
    dynamic_fields['__module__'] = __name__

    class Meta:
        managed = False
        db_table = document.code

    dynamic_fields['Meta'] = Meta

    model_name = f"{document.code.capitalize()}DynamicModel"
    dynamic_model = type(model_name, (models.Model,), dynamic_fields)
    return dynamic_model