"""
Abstract base models
"""
from django.db import models
from django.contrib.postgres.fields import ArrayField
from .config import default_name, START_STEP, STEP_SORT
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
    LIST_INTEGERS = 'list_integers', 'List Integers'
    LIST_STRING = 'list_string', 'List String'


class TimeStampedModel(models.Model):
    """
    Abstract model with created_at, updated_at and deleted_at fields.
    """
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Created at')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Updated at')
    deleted_at = models.DateTimeField(null=True, blank=True, verbose_name='Deleted at')

    class Meta:
        abstract = True


class NonDeleted(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)


class SoftDelete(models.Model):
    """
    Abstract model for soft deletion logic.
    """
    is_deleted = models.BooleanField(default=False, verbose_name='Is deleted')
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


class AutoSortModel(models.Model):
    """
    Abstract model that automatically increments index_sort on first save.
    """
    index_sort = models.PositiveBigIntegerField(blank=True, verbose_name='Sort index')

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if not self.pk and self.index_sort is None:
            max_sort = self.__class__.objects.aggregate(models.Max('index_sort'))['index_sort__max']
            if max_sort is None:
                max_sort = START_STEP
            self.index_sort = max_sort + STEP_SORT
        super().save(*args, **kwargs)


class IndicatorBase(TimeStampedModel, AutoSortModel):
    """
    Base indicator abstraction.
    """
    short_name = models.JSONField(verbose_name='Short name', default=default_name)
    full_name = models.JSONField(verbose_name='Full name', default=default_name, null=True, blank=True)
    description = models.JSONField(verbose_name='Description', default=default_name, null=True, blank=True)
    code = models.CharField(max_length=128, verbose_name='Code', unique=True)
    active = models.BooleanField(default=True, verbose_name='Active')
    type_value = models.CharField(
        max_length=64, choices=IndicatorType.choices, default=IndicatorType.STRING, verbose_name='Value type')
    type_extend = models.CharField(max_length=128, null=True, blank=True, verbose_name='Type extension')
    is_filtered = models.BooleanField(default=False, verbose_name='Add to filter')
    is_multiple = models.BooleanField(default=False, verbose_name='Multiple choice')
    is_required = models.BooleanField(default=False, verbose_name='Required field')

    class Meta:
        abstract = True


class IndicatorValueBase(TimeStampedModel, AutoSortModel):
    """
    Base class for indicator values.
    """
    value_json = models.JSONField(null=True, blank=True, verbose_name='JSON value')
    value_int = models.BigIntegerField(null=True, blank=True, verbose_name='Integer value')
    value_float = models.FloatField(null=True, blank=True, verbose_name='Float value')
    value_str = models.CharField(max_length=255, null=True, blank=True, verbose_name='String value')
    value_text = models.TextField(null=True, blank=True, verbose_name='Text value')
    value_datetime = models.DateTimeField(null=True, blank=True, verbose_name='Datetime value')
    value_bool = models.BooleanField(null=True, blank=True, verbose_name='Boolean value')
    value_reference = models.PositiveBigIntegerField(null=True, blank=True, verbose_name='Foreign key value')
    value_array_int = ArrayField(models.PositiveIntegerField(), blank=True, default=list, verbose_name='Integer list')
    value_array_str = ArrayField(models.CharField(max_length=255), blank=True, default=list, verbose_name='String list')
    active = models.BooleanField(default=True, verbose_name='Active')

    class Meta:
        abstract = True

    @staticmethod
    def json_file_data(filename, file_id):
        return json.dumps({"filename": filename, "file_id": file_id})


class CommonManager(models.Manager):
    def get_by_code(self, code):
        return self.get(code=code).id

    def get_id_by_code(self, id):
        return self.get(id=id).code

    def get_by_list_and_code(self, list_id, code):
        return self.get(list_id=list_id, code=code).id
