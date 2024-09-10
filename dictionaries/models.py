from IEF.base_model import CategoryBase, IndicatorBase, ParameterBase, IndicatorValueBase, default_map, Enum
from users.models import User
from django.db import models
import json


class ABCDictionary(models.Model):
    """
    Абстракция справочника
    """
    name = models.JSONField(verbose_name='Наименование', default=default_map)
    description = models.JSONField(
        null=True, blank=True, verbose_name='Описание', default=default_map)
    code = models.CharField(
        max_length=128, verbose_name='Код', unique=True)
    author = models.ForeignKey(
        to=User, on_delete=models.SET_NULL, null=True, verbose_name='Автор')
    active = models.BooleanField(
        default=True, verbose_name='Активный')

    def __str__(self):
        return self.name.get("ru", self.code)

    class Meta:
        db_table = '"dct\".\"abc_dictionary"'
        verbose_name = 'Справочник'
        verbose_name_plural = 'Справочники'


class Indicator(IndicatorBase):
    """
    Показатели :ABCDictionary
    """
    abc_dictionary = models.ForeignKey(
        to=ABCDictionary, on_delete=models.CASCADE, verbose_name='Справочник',
        related_name='indicator')
    reference = models.ForeignKey(
        to=ABCDictionary, on_delete=models.CASCADE, verbose_name='Внешний ключ',
        null=True, blank=True, related_name='reference')
    author = models.ForeignKey(to=User, on_delete=models.SET_NULL, null=True, verbose_name='Автор',
                               related_name="indicator_author")

    def __str__(self):
        return self.name.get("ru", self.code)

    class Meta:
        db_table = '"dct\".\"indicator"'
        verbose_name = 'Индикатор'
        verbose_name_plural = 'Индикаторы'

    def save(self, *args, **kwargs):
        """
        Счетчик сортировки +5
        """
        if not self.pk:  # If the object is being created (not updated)
            # Get the maximum value of index_sort from existing records
            max_sort = Indicator.objects.aggregate(models.Max('index_sort'))['index_sort__max']
            # If max_sort is None (meaning there are no records), start at 0
            if max_sort is None:
                max_sort = 0
            self.index_sort = max_sort + 5
        super().save(*args, **kwargs)


class Element(models.Model):
    """
    Элементы :ABCDictionary
    """
    short_name = models.JSONField(
        verbose_name='Краткое наименование', default=default_map)
    full_name = models.JSONField(
        verbose_name='Краткое наименование', null=True, blank=True, default=default_map)
    code = models.CharField(
        max_length=128, verbose_name='Код', unique=True)
    abc_dictionary = models.ForeignKey(
        to=ABCDictionary, on_delete=models.SET_NULL, null=True, verbose_name='Справочник')
    parent = models.ForeignKey(
        "self", null=True, blank=True, related_name="children",
        on_delete=models.CASCADE, verbose_name='Родительский элемент')
    active = models.BooleanField(
        default=True, verbose_name='Активный')
    author = models.ForeignKey(
        to=User, on_delete=models.SET_NULL, null=True, verbose_name='Автор', related_name="element")

    def __str__(self):
        return self.short_name.get("ru")

    class Meta:
        db_table = '"dct\".\"element"'
        verbose_name = 'Элемент'
        verbose_name_plural = 'Элементы'


class ElementIndicatorValue(IndicatorValueBase):
    """
    Значения индикаторов по Элементам
    """
    element = models.ForeignKey(
        to=Element, on_delete=models.CASCADE, verbose_name='Элемент',
        related_name="element_value")
    indicator = models.ForeignKey(
        to=Indicator, on_delete=models.CASCADE, verbose_name='Показатель',
        related_name="indicator_value")
    author = models.ForeignKey(
        to=User, on_delete=models.SET_NULL, null=True, verbose_name='Автор')

    class Meta:
        db_table = '"dct\".\"indicator_value"'
        verbose_name = 'Значение инициатора'
        verbose_name_plural = 'Значение индикаторов'

    def __str__(self):
        return self.value_str or str(self.value_int) or self.value_text or str(self.value_datetime)

    def save(self, *args, **kwargs):
        """Автоматическое заполнение сортировки"""
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


class ElementHistory(models.Model):
    """
    Истрория действии над :Elements
    """
    stamp = models.JSONField(verbose_name='Слепок', null=True, blank=True)
    action = models.CharField(max_length=128, null=True, blank=True, verbose_name='Действие')
    element = models.ForeignKey(
        to=Element, on_delete=models.SET_NULL, null=True, verbose_name='Элемент',
        related_name="element_history")
    author = models.ForeignKey(
        to=User, on_delete=models.SET_NULL, null=True, verbose_name='Автор')
    created_at = models.DateTimeField(
        auto_now_add=True, blank=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(
        auto_now=True, blank=True, verbose_name='Дата обновления')

    class Meta:
        db_table = '"dct\".\"element_history"'
        verbose_name = 'История элемента'
        verbose_name_plural = 'История элементов'

    def __str__(self):
        return self.action
