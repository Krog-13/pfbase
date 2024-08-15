from django.db import models
from users.models import Organization
from users.models import User
from django.conf import settings
import json
import pytz
from datetime import datetime


class CategoryBase(models.Model):
    """
    Базовая модель для категорий/документов/справочников
    """
    short_name = models.CharField(
        max_length=128, unique=True, verbose_name='Наименование')
    description = models.TextField(
        null=True, blank=True, verbose_name='Описание')
    index_sort = models.PositiveIntegerField(
        null=True, blank=True, verbose_name="Сортировка", default=1)
    parent = models.ForeignKey("self", null=True, blank=True, related_name="children", on_delete=models.SET_NULL,
                               verbose_name='Родительская категория')

    def __str__(self):
        return self.short_name

    class Meta:
        abstract = True
        managed = False


class EntityBase(models.Model):
    """
    Базовая модель для отчетов/показателей
    """

    naming = models.JSONField(
        max_length=255, verbose_name='Наименование', null=True, blank=True)
    description = models.TextField(
        null=True, blank=True, verbose_name='Описание')
    code = models.CharField(max_length=128, verbose_name='Код')
    organizations = models.ManyToManyField(
        to=Organization, blank=True, verbose_name='Организация')

    def __str__(self):
        return self.code

    class Meta:
        abstract = True
        managed = False


class IndicatorBase(models.Model):
    """
    Базовая модель для показателей
    """
    _TYPE_VALUE = [("int", "integer"), ("float", "float"), ("bool", "boolean"), ("list", "list"),
                   ("date", "datetime"), ("str", "string"), ("file", "file"), ("text", "text"),
                   ("dct", "dictionary"), ("dcm", "document"), ("rpt", "report"), ("calc", "calculate")]
    short_name = models.CharField(
        max_length=255, verbose_name='Наименование')
    type_value = models.CharField(
        max_length=128, choices=_TYPE_VALUE, default="str", verbose_name='Тип')

    def __str__(self):
        return self.short_name

    class Meta:
        abstract = True
        managed = False


class DefaultParameterBase(models.Model):
    """
    Базовая модель для параметров
    """
    short_name = models.CharField(
        max_length=128, verbose_name='Наименование параметра')

    def __str__(self):
        return self.short_name

    class Meta:
        abstract = True
        managed = False  # False для того, чтобы не создавалась таблица в БД


class OutputEntityBase(models.Model):
    """
    Базовая модель для выходных отчетов
    """
    status = models.CharField(
        max_length=128, verbose_name='Статус')
    date_time = models.DateTimeField(verbose_name='Дата создания', null=True)
    author = models.ForeignKey(
        to=User, on_delete=models.CASCADE, verbose_name='Автор')

    def create(self, report_status, report_id, user_id):
        pass

    def save(self, *args, **kwargs):
        self.date_time = datetime.now(pytz.timezone(settings.TIME_ZONE)).strftime("%Y-%m-%d %H:%M:%S %Z")
        super().save(*args, **kwargs)

    class Meta:
        abstract = True
        managed = False


class IndicatorValueBase(models.Model):
    """
    Базовая модель для значений показателей
    """
    indicator_value = models.CharField(
        max_length=255, null=True, blank=True, verbose_name='Значение')

    class Meta:
        abstract = True
        managed = False  # Set managed to False to prevent migrations for this model

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
