from django.db.models import TextChoices
from django.db import models
from django.contrib.postgres.fields import ArrayField


class IndicatorType(TextChoices):
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
    IndicatorType.LIST_INTEGERS: 'value_array_int',
    IndicatorType.LIST_STRING: 'value_array_str',
}

MAPPING = {
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
        IndicatorType.LIST: models.IntegerField,
        IndicatorType.DICTIONARY: models.PositiveBigIntegerField,
        IndicatorType.DOCUMENT: models.PositiveBigIntegerField,
        IndicatorType.CALCULATE: models.CharField,
        IndicatorType.USER: models.PositiveBigIntegerField,
        IndicatorType.ORGANIZATION: models.PositiveBigIntegerField,
        IndicatorType.LIST_INTEGERS: lambda **kwargs: ArrayField(models.PositiveIntegerField(), **kwargs),
        IndicatorType.LIST_STRING: lambda **kwargs: ArrayField(models.CharField(), **kwargs),
    }

INDICATOR_FOR_MULTIPLE_STR_UPLOAD = [
    IndicatorType.STRING,
    IndicatorType.TEXT,
    IndicatorType.DATE,
    IndicatorType.DATETIME,
    IndicatorType.FILE,
    IndicatorType.TIME
]

INDICATOR_FOR_MULTIPLE_INT_UPLOAD = [
    IndicatorType.INTEGER,
    IndicatorType.FLOAT,
    IndicatorType.BOOLEAN,
    IndicatorType.DATETIME,
    IndicatorType.FILE,
    IndicatorType.LIST,
    IndicatorType.DICTIONARY,
    IndicatorType.DOCUMENT,
    IndicatorType.USER,
    IndicatorType.ORGANIZATION
]