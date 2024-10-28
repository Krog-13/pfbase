from pfbase.base_models import IndicatorValueBase
from .indicators import DcmIndicators
from .records import Records
from django.db import models
from pfbase import config
import json


class RecordIndicatorValues(IndicatorValueBase):
    """
    Значения индикаторов по Записям
    """
    record = models.ForeignKey(
        to=Records, on_delete=models.CASCADE, verbose_name='Запись',
        related_name="record_values")
    indicator = models.ForeignKey(
        to=DcmIndicators, on_delete=models.CASCADE, verbose_name='Показатель',
        related_name="indicator_values")

    def __str__(self):
        if self.value_str:
            return self.value_str
        elif self.value_text:
            return self.value_text[:10]
        elif self.value_datetime:
            return str(self.value_datetime)
        elif self.value_int:
            return str(self.value_int)
        elif self.value_bool:
            return str(self.value_bool)
        elif self.value_reference:
            return str(self.value_reference)
        else:
            return "No data"

    class Meta:
        db_table = '"dcm\".\"record_indicator_values"'
        verbose_name = 'DCM Значение инидкатора'
        verbose_name_plural = 'DCM Значения индикаторов'

    @staticmethod
    def json_file_data(filename, file_id):
        file_data = {"filename": filename, "file_id": file_id}
        return json.dumps(file_data)

    def save(self, *args, **kwargs):
        """Автоматическое заполнение сортировки"""
        if not self.pk:
            max_sort = RecordIndicatorValues.objects.aggregate(models.Max('index_sort'))['index_sort__max']
            if max_sort is None:
                max_sort = 0
            self.index_sort = max_sort + config.STEP_SORT
        super().save(*args, **kwargs)
