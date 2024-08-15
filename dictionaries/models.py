from django.db import models
import json
from IEF.base_model import CategoryBase, IndicatorBase, DefaultParameterBase, IndicatorValueBase
from users.models import Organization, User


class CategoryDictionary(CategoryBase):
    """
    Категории справочников
    """
    class Meta:
        db_table = '"dct\".\"categories"'
        verbose_name = 'Категорию справочника'
        verbose_name_plural = 'Категории справочников'


class ABCDictionary(models.Model):
    """
    Абстракция справочников
    """

    naming = models.JSONField(
        max_length=255, verbose_name='Наименование', null=True, blank=True)
    description = models.TextField(
        null=True, blank=True, verbose_name='Описание')
    abc_code = models.CharField(max_length=128, verbose_name='Код', null=True, blank=True)
    organizations = models.ManyToManyField(
        to=Organization, blank=True, verbose_name='Организация')
    category_dictionary = models.ForeignKey(
        CategoryDictionary, null=True, blank=True, on_delete=models.SET_NULL, verbose_name='Категория справочника')
    author = models.ForeignKey(
        to=User, on_delete=models.CASCADE, verbose_name='Автор')

    def __str__(self):
        return self.naming["short_name"]

    class Meta:
        db_table = '"dct\".\"abc_dictionary"'
        verbose_name = 'Справочник'
        verbose_name_plural = 'Справочники'

    def save(self, *args, **kwargs):
        if self.full_name or self.part_name:
            self.naming = {"full_name": self.full_name, "short_name": self.part_name}
        super().save(*args, **kwargs)


class Element(models.Model):
    """
    Elements
    """
    short_name = models.CharField(
        max_length=128, unique=True, verbose_name='Наименование')
    code = models.CharField(max_length=128, verbose_name='Код')
    abc_dictionary = models.ForeignKey(to=ABCDictionary, null=True, blank=True, on_delete=models.SET_NULL, verbose_name='Справочник')
    parent = models.ForeignKey("self", null=True, blank=True, related_name="children", on_delete=models.SET_NULL,
                               verbose_name='Родительский элемент')

    def __str__(self):
        return self.short_name

    class Meta:
        db_table = '"dct\".\"element"'
        verbose_name = 'Элемент'
        verbose_name_plural = 'Элементы'


class IndicatorParameter(DefaultParameterBase):
    """
    Параметры показателей
    """

    class Meta:
        db_table = '"dct\".\"default_parameter"'
        verbose_name = 'Параметр'
        verbose_name_plural = 'Параметры'


class DictionaryIndicator(IndicatorBase):
    """
    Показатели
    """
    idc_code = models.CharField(max_length=128, verbose_name='Код', null=True, blank=True)
    dictionary = models.ForeignKey(
        to=ABCDictionary, on_delete=models.CASCADE, verbose_name='Справочник', related_name='dictionary_indicators')
    type_reference = models.ForeignKey(
        to=ABCDictionary, on_delete=models.CASCADE, verbose_name='Тип Справочника', null=True, blank=True,
        related_name='type_reference_indicators')
    parameters = models.ManyToManyField(
        IndicatorParameter, blank=True, verbose_name='Параметры')

    def __str__(self):
        return self.short_name + " " + f"({self.dictionary.naming['short_name']})"

    class Meta:
        db_table = '"dct\".\"indicator"'
        verbose_name = 'Показатель'
        verbose_name_plural = 'Показатели'


class DictionaryIndicatorValue(IndicatorValueBase):
    """
    Значения показателей
    """
    element = models.ForeignKey(
        to=Element, on_delete=models.CASCADE, verbose_name='Элемент', related_name="indicator")
    indicator = models.ForeignKey(
        to=DictionaryIndicator, on_delete=models.CASCADE, verbose_name='Показатель', related_name="dictionaryindicator")

    class Meta:
        db_table = '"dct\".\"indicator_value"'
        verbose_name = 'Значение показателя'
        verbose_name_plural = 'Значение показателей'

    def __str__(self):
        return self.indicator_value if self.indicator_value else "None"

    @staticmethod
    def json_file_data(filename, file_id):
        file_data = {"filename": filename, "file_id": file_id}
        return json.dumps(file_data)
