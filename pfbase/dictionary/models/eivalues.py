from pfbase.base_models import IndicatorValueBase
from django.db import models
from .indicators import DctIndicators
from .elements import Elements
from pfbase.dictionary.manager import ElementsIndicatorValueManager


class ElementIndicatorValues(IndicatorValueBase):
    """
    Indicator values for :Elements
    """
    element = models.ForeignKey(
        to=Elements, on_delete=models.CASCADE, verbose_name='Element',
        related_name="element_values")
    indicator = models.ForeignKey(
        to=DctIndicators, on_delete=models.CASCADE, verbose_name='Indicator',
        related_name="indicator_values")
    author = models.ForeignKey(
        to="User", on_delete=models.SET_NULL, null=True, verbose_name='Author')

    objects = ElementsIndicatorValueManager()

    class Meta:
        db_table = '"dct\".\"element_indicator_values"'
        verbose_name = 'DCT Indicator Value'
        verbose_name_plural = 'DCT Indicator Values'

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
        elif self.value_json:
            return "JSON data"
        else:
            return "No data"
