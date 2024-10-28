from pfbase.base_models import IndicatorValueBase
from .indicators import DctIndicators
from .elements import Elements
from django.db import models
from pfbase import config
import json


class ElementIndicatorValues(IndicatorValueBase):
    """
    Значения индикаторов по Элементам
    """
    element = models.ForeignKey(
        to=Elements, on_delete=models.CASCADE, verbose_name='Элемент',
        related_name="element_values")
    indicator = models.ForeignKey(
        to=DctIndicators, on_delete=models.CASCADE, verbose_name='Показатель',
        related_name="indicator_values")
    author = models.ForeignKey(
        to="User", on_delete=models.SET_NULL, null=True, verbose_name='Автор')

    class Meta:
        db_table = '"dct\".\"element_indicator_values"'
        verbose_name = 'DCT Значение инициатора'
        verbose_name_plural = 'DCT Значение индикаторов'

    def __str__(self):
        return self.value_str or str(self.value_int) or self.value_text[:10] or str(self.value_datetime)

    def save(self, *args, **kwargs):
        """Автоматическое заполнение сортировки"""
        if not self.pk:
            max_sort = ElementIndicatorValues.objects.aggregate(models.Max('index_sort'))['index_sort__max']
            if max_sort is None:
                max_sort = 0
            self.index_sort = max_sort + config.STEP_SORT
        super().save(*args, **kwargs)

    @staticmethod
    def json_file_data(filename, file_id):
        file_data = {"filename": filename, "file_id": file_id}
        return json.dumps(file_data)
