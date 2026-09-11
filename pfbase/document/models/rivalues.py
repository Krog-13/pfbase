from pfbase.base_models import IndicatorValueBase
from django.db import models
from .indicators import DcmIndicators
from .records import Records


class RecordIndicatorValues(IndicatorValueBase):
    """
    Indicator values for :Records
    """
    record = models.ForeignKey(
        to=Records, on_delete=models.CASCADE, verbose_name='Record',
        related_name="record_values")
    indicator = models.ForeignKey(
        to=DcmIndicators, on_delete=models.CASCADE, verbose_name='Indicator',
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
        elif self.value_float:
            return str(self.value_float)
        elif self.value_bool:
            return str(self.value_bool)
        elif self.value_reference:
            return str(self.value_reference)
        elif self.value_array_str:
            return "Array of string"
        elif self.value_array_int:
            return "Array of integer"
        elif self.value_json:
            return "JSON data"
        else:
            return "No data"

    class Meta:
        db_table = '"dcm\".\"record_indicator_values"'
        verbose_name = 'DCM Indicator Value'
        verbose_name_plural = 'DCM Indicator Values'
