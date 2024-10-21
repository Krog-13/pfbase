"""
Abstract base models
"""
from django.db import models
from .config import default_map
import json


class IndicatorBase(models.Model):
    """
    Базовый класс индикаторы
    """
    _TYPE_VALUE = [("str", "string"), ("int", "integer"), ("float", "float"), ("bool", "boolean"), ("list", "list"),
                   ("datetime", "datetime"), ("date", "date"), ("time", "time"), ("text", "text"),
                   ("file", "file"), ("dct", "dictionary"), ("dcm", "document"),
                   ("calc", "calculate"), ("user", "user"), ("org", "organization")]
    name = models.JSONField(verbose_name='Наименование', default=default_map)
    description = models.JSONField(
        null=True, blank=True, verbose_name='Описание', default=default_map)
    index_sort = models.PositiveIntegerField(unique=True, blank=True, verbose_name='Индекс сортировки')
    code = models.CharField(
        max_length=128, verbose_name='Код', unique=True)
    active = models.BooleanField(
        default=True, blank=True, verbose_name='Активный')
    type_value = models.CharField(
        max_length=64, choices=_TYPE_VALUE, default="str", verbose_name='Тип')
    type_extend = models.CharField(
        max_length=128, null=True, blank=True, verbose_name='Тип расширения')

    class Meta:
        abstract = True
        managed = False


class ParameterBase(models.Model):
    """
    Базовый класс параметров по умолчанию
    """
    short_name = models.JSONField(verbose_name='Краткое наименование')
    active = models.BooleanField(
        default=True, blank=True, verbose_name='Активный')

    def __str__(self):
        return self.short_name.get("ru")

    class Meta:
        abstract = True
        managed = False


class IndicatorValueBase(models.Model):
    """
    Базовый класс значений индикаторов
    """
    value_json = models.JSONField(
        null=True, blank=True, verbose_name='Json значение')
    value_int = models.IntegerField(
        null=True, blank=True, verbose_name='Целое число')
    value_str = models.CharField(
        max_length=255, null=True, blank=True, verbose_name='Строка')
    value_text = models.TextField(
        null=True, blank=True, verbose_name='Текст')
    value_datetime = models.DateTimeField(
        null=True, blank=True, verbose_name='Дата и время')
    value_bool = models.BooleanField(
        null=True, blank=True, verbose_name='Логическое значение')
    value_reference = models.PositiveIntegerField(
        null=True, blank=True, verbose_name='Внешний ключ')
    index_sort = models.PositiveIntegerField(
        unique=True, blank=True, verbose_name='Индекс сортировки')
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
