"""
Abstract base models
"""
from django.contrib.postgres.fields import ArrayField
from django.db import models
from .config import default_name
import json


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


class IndicatorBase(models.Model):
    """
    Базовый класс индикаторы
    """
    short_name = models.JSONField(verbose_name='Краткое наименование', default=default_name)
    full_name = models.JSONField(verbose_name='Полное наименование',
                                 default=default_name, null=True, blank=True)
    description = models.JSONField(
        null=True, blank=True, verbose_name='Описание', default=default_name)
    index_sort = models.PositiveIntegerField(blank=True, verbose_name='Индекс сортировки')
    code = models.CharField(
        max_length=128, verbose_name='Код', unique=True)
    active = models.BooleanField(
        default=True, blank=True, verbose_name='Активный')
    type_value = models.CharField(
        max_length=64, choices=IndicatorType.choices, default=IndicatorType.STRING, verbose_name='Тип значения')
    type_extend = models.CharField(
        max_length=128, null=True, blank=True, verbose_name='Расширения типа')
    is_filtered = models.BooleanField(
        default=False, blank=True, verbose_name='Добавить в фильтр')
    is_multiple = models.BooleanField(
        default=False, blank=True, verbose_name="Множественный выбор")

    class Meta:
        abstract = True
        managed = False


class IndicatorValueBase(models.Model):
    """
    Базовый класс значений индикаторов
    """
    value_json = models.JSONField(
        null=True, blank=True, verbose_name='Json значение')
    value_int = models.BigIntegerField(
        null=True, blank=True, verbose_name='Целое число')
    value_float = models.FloatField(
        null=True, blank=True, verbose_name='Дробное число')
    value_str = models.CharField(
        max_length=255, null=True, blank=True, verbose_name='Строка')
    value_text = models.TextField(
        null=True, blank=True, verbose_name='Текст')
    value_datetime = models.DateTimeField(
        null=True, blank=True, verbose_name='Дата и время')
    value_bool = models.BooleanField(
        null=True, blank=True, verbose_name='Логическое значение')
    value_reference = models.PositiveBigIntegerField(
        null=True, blank=True, verbose_name='Внешний ключ')
    value_array_int = ArrayField(
        models.PositiveIntegerField(),
        blank=True, default=list, verbose_name="Список Int")
    value_array_str = ArrayField(
        models.CharField(max_length=128),
        blank=True, default=list, verbose_name="Список Str")
    index_sort = models.PositiveBigIntegerField(
        blank=True, verbose_name='Индекс сортировки')
    active = models.BooleanField(
        default=True, blank=True, verbose_name='Активный')

    class Meta:
        abstract = True
        managed = False

    @staticmethod
    def json_file_data(filename, file_id):
        file_data = {"filename": filename, "file_id": file_id}
        return json.dumps(file_data)


class NonDeleted(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)


class SoftDelete(models.Model):
    is_deleted = models.BooleanField(default=False)
    everything = models.Manager()
    objects = NonDeleted()

    def soft_delete(self):
        self.is_deleted = True
        self.save()

    def restore(self):
        self.is_deleted = False
        self.save()

    class Meta:
        abstract = True


class CommonManager(models.Manager):
    def getByCode(self, code):
        return self.get(code=code).id

    def getById(self, id):
        return self.get(id=id).code

    def getByListAndCode(self, list, code):
        return self.get(list=list, code=code).id

    def getAll(self):
        return self.all()
