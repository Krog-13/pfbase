from django.conf import settings
from users.models import User
from datetime import datetime
from django.db import models
import json
import pytz


def default_map():
    return {"ru": "", "kz": "", "en": ""}


class CategoryBase(models.Model):
    """
    Base model for document/dictionary
    """
    short_name = models.CharField(
        max_length=128, unique=True, verbose_name='Наименование')
    parent = models.ForeignKey(
        "self", null=True, blank=True, related_name="children", on_delete=models.CASCADE,
        verbose_name='Родительская категория')

    def __str__(self):
        return self.short_name

    class Meta:
        abstract = True
        managed = False


class IndicatorBase(models.Model):
    """
    Base model for indicators
    """
    _TYPE_VALUE = [("str", "string"), ("int", "integer"), ("float", "float"), ("bool", "boolean"), ("list", "list"),
                   ("datetime", "datetime"), ("date", "date"), ("time", "time"), ("text", "text"),
                   ("file", "file"), ("enum", "enum"), ("dct", "dictionary"), ("dcm", "document"),
                   ("calc", "calculate")]
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
    Base model for parameters
    """
    short_name = models.JSONField(verbose_name='Краткое наименование')
    active = models.BooleanField(
        default=True, blank=True, verbose_name='Активный')

    def __str__(self):
        return self.short_name.get("ru")

    class Meta:
        abstract = True
        managed = False  # False для того, чтобы не создавалась таблица в БД


class IndicatorValueBase(models.Model):
    """
    Base model for indicator values
    """
    value_int = models.IntegerField(
        null=True, blank=True, verbose_name='Целое число')
    value_str = models.CharField(
        max_length=255, null=True, blank=True, verbose_name='Строка')
    value_text = models.TextField(
        null=True, blank=True, verbose_name='Текст')
    value_datetime = models.DateTimeField(
        null=True, blank=True, verbose_name='Дата и время')
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


class Enum(models.Model):
    """Enum"""
    list = models.CharField(max_length=128, unique=True, verbose_name='Код списка')
    code = models.CharField(max_length=128, verbose_name='Код элемента')
    short_name = models.JSONField(
        verbose_name='Краткое наименование', default=default_map)
    full_name = models.JSONField(
        verbose_name='Полное наименование', null=True, blank=True, default=default_map)
    active = models.BooleanField(default=True, verbose_name='Активный')
    author = models.ForeignKey(
        to=User, on_delete=models.CASCADE, verbose_name='Автор', related_name="enum")

    def __str__(self):
        return self.list

    class Meta:
        verbose_name = 'Перечисление'
        verbose_name_plural = 'Перечисления'


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
