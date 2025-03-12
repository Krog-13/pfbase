from django.db.models import Subquery, OuterRef
from django.core.exceptions import ImproperlyConfigured, ObjectDoesNotExist
from pfbase.document.models.rivalues import *
from pfbase.document.models.indicators import *
from pfbase.system.models.user import User
from pfbase.system.models.organization import Organization
from pfbase.business_values_fields import IndicatorType, MAPPING, INDICATOR_TO_VALUE_FIELD, INDICATOR_FOR_MULTIPLE_STR_UPLOAD, INDICATOR_FOR_MULTIPLE_INT_UPLOAD
from rest_framework import serializers


def get_field_class_for_indicator(indicator):
    field_class = MAPPING.get(indicator.type_value)
    if not field_class:
        raise ImproperlyConfigured(f"Тип индикатора {indicator.type_value} не поддерживается")
    return field_class


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


class BusinessDocumentModelManager(models.Manager):
    def __init__(self, document, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.document = document

    def get_queryset(self):
        qs = Records.objects.filter(document=self.document).select_related('author', 'document', 'parent',
                                                                           'organization')
        for indicator in self.document.indicators.all():
            value_field = get_target_field(indicator)
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
                target_field = get_target_field(indicator)
                if indicator.is_multiple and indicator.type_value in INDICATOR_FOR_MULTIPLE_STR_UPLOAD:
                    value = value.split(';')
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
                target_field = get_target_field(indicator)

                try:
                    indicator_value = RecordIndicatorValues.objects.get(record=instance, indicator=indicator)
                    setattr(indicator_value, target_field, value)
                    indicator_value.save()
                except RecordIndicatorValues.DoesNotExist:
                    RecordIndicatorValues.objects.create(
                        record=instance,
                        indicator=indicator,
                        **{target_field: value},
                    )
        return instance

    def delete_instance(self, instance):
        RecordIndicatorValues.objects.filter(record=instance).delete()
        instance.delete()


_BUSINESS_DOCUMENT_MODEL_CACHE = {}


def BusinessDocumentModel(document_code):
    if document_code in _BUSINESS_DOCUMENT_MODEL_CACHE:
        return _BUSINESS_DOCUMENT_MODEL_CACHE[document_code]

    try:
        document = Documents.objects.get(code=document_code)
    except ObjectDoesNotExist:
        raise ValueError(f"Документ с кодом '{document_code}' не найден")

    dynamic_fields = {
        'id': models.AutoField(primary_key=True),
        'number': models.CharField(max_length=255, verbose_name="Номер", null=True),
        'date': models.DateTimeField(verbose_name="Дата", null=True),
        'active': models.BooleanField(default=True, verbose_name="Активный"),
        'parent': models.ForeignKey('self', null=True, blank=True, related_name="children", on_delete=models.CASCADE, verbose_name='Родительская запись'),
        'author': models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Автор'),
        'organization': models.ForeignKey(Organization, on_delete=models.SET_NULL, blank=True, null=True, verbose_name='Организация'),
    }

    for indicator in document.indicators.all().select_related('document','author'):
        field_class = get_field_class_for_indicator(indicator)
        field_kwargs = {'null': True, 'blank': True, 'verbose_name': indicator.short_name.get("ru", indicator.code)}
        if field_class == models.CharField:
            field_kwargs.setdefault('max_length', 255)
        dynamic_fields[indicator.code] = field_class(**field_kwargs)

    dynamic_fields['objects'] = BusinessDocumentModelManager(document)
    dynamic_fields['__module__'] = __name__

    class Meta:
        managed = False
        db_table = document.code

    dynamic_fields['Meta'] = Meta
    model_name = f"{document.code.capitalize()}_BusinessModel"
    business_model = type(model_name, (models.Model,), dynamic_fields)
    parent_field = business_model._meta.get_field('parent')
    parent_field.remote_field.model = business_model

    for indicator in document.indicators.all():
        field_name = indicator.code

        def getter(self, field_name=field_name):
            return self.__dict__.get(field_name)

        setattr(business_model, field_name, property(getter))

    _BUSINESS_DOCUMENT_MODEL_CACHE[document_code] = business_model
    return business_model

