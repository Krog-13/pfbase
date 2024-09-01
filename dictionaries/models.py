from IEF.base_model import CategoryBase, IndicatorBase, ParameterBase, IndicatorValueBase
from users.models import User
from django.db import models
import json


class Category(CategoryBase):
    """
    Category of dictionaries
    """
    class Meta:
        db_table = '"dct\".\"categories"'
        verbose_name = 'Категорию справочника'
        verbose_name_plural = 'Категории справочников'


class ABCDictionary(models.Model):
    """
    Abstract Dictionary
    """
    dct_name = models.JSONField(verbose_name='Наименование')
    description = models.TextField(
        null=True, blank=True, verbose_name='Описание')
    code = models.CharField(
        max_length=128, verbose_name='Код', unique=True)
    category = models.ForeignKey(
        Category, null=True, blank=True, on_delete=models.SET_NULL,
        verbose_name='Категория справочника')
    author = models.ForeignKey(
        to=User, on_delete=models.SET_NULL, null=True, verbose_name='Автор')

    def __str__(self):
        return self.dct_name.get("short_name", self.code)

    class Meta:
        db_table = '"dct\".\"abc_dictionary"'
        verbose_name = 'Справочник'
        verbose_name_plural = 'Справочники'

    def save(self, *args, **kwargs):
        if self.full_name or self.part_name:
            self.dct_name = {"full_name": self.full_name, "short_name": self.part_name}
        super().save(*args, **kwargs)


class IndicatorParameter(ParameterBase):
    """
    Default parameters for indicators
    """
    class Meta:
        db_table = '"dct\".\"idc_parameter"'
        verbose_name = 'Параметр'
        verbose_name_plural = 'Параметры'


class Indicator(IndicatorBase):
    """
    Indicator for dictionaries
    """
    abc_dictionary = models.ForeignKey(
        to=ABCDictionary, on_delete=models.CASCADE, verbose_name='Справочник',
        related_name='indicator')
    reference = models.ForeignKey(
        to=ABCDictionary, on_delete=models.CASCADE, verbose_name='Внешний ключ',
        null=True, blank=True, related_name='reference')
    parameters = models.ManyToManyField(
        IndicatorParameter, blank=True, verbose_name='Параметры')

    def __str__(self):
        return self.short_name.get("ru", self.code)

    class Meta:
        db_table = '"dct\".\"indicator"'
        verbose_name = 'Индикатор'
        verbose_name_plural = 'Индикаторы'

    def save(self, *args, **kwargs):
        if not self.pk:  # If the object is being created (not updated)
            # Get the maximum value of index_sort from existing records
            max_sort = Indicator.objects.aggregate(models.Max('index_sort'))['index_sort__max']

            # If max_sort is None (meaning there are no records), start at 0
            if max_sort is None:
                max_sort = 0

            # Increment by 5
            self.index_sort = max_sort + 5

        super().save(*args, **kwargs)


class Element(models.Model):
    """
    Elements
    """
    short_name = models.JSONField(verbose_name='Краткое наименование')
    abc_dictionary = models.ForeignKey(
        to=ABCDictionary, on_delete=models.SET_NULL, null=True, verbose_name='Справочник')
    parent = models.ForeignKey(
        "self", null=True, blank=True, related_name="children",
        on_delete=models.CASCADE, verbose_name='Родительский элемент')

    def __str__(self):
        return self.short_name.get("ru")

    class Meta:
        db_table = '"dct\".\"element"'
        verbose_name = 'Элемент'
        verbose_name_plural = 'Элементы'


class ElementIndicatorValue(IndicatorValueBase):
    """
    Element-Indicator Value
    """
    element = models.ForeignKey(
        to=Element, on_delete=models.CASCADE, verbose_name='Элемент',
        related_name="element_value")
    indicator = models.ForeignKey(
        to=Indicator, on_delete=models.CASCADE, verbose_name='Показатель',
        related_name="indicator_value")

    class Meta:
        db_table = '"dct\".\"indicator_value"'
        verbose_name = 'Значение показателя'
        verbose_name_plural = 'Значение показателей'

    def __str__(self):
        return self.value_str or str(self.value_int)

    def save(self, *args, **kwargs):
        if not self.pk:
            max_sort = ElementIndicatorValue.objects.aggregate(models.Max('index_sort'))['index_sort__max']
            if max_sort is None:
                max_sort = 0
            self.index_sort = max_sort + 5
        super().save(*args, **kwargs)

    @staticmethod
    def json_file_data(filename, file_id):
        file_data = {"filename": filename, "file_id": file_id}
        return json.dumps(file_data)
