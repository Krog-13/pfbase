from pfbase.base_models import IndicatorBase
from pfbase.dictionary.manager import IndicatorsManager
from django.db import models
from .dictionaries import Dictionaries


class DctIndicators(IndicatorBase):
    """
    Indicators for :Dictionaries
    """
    dictionary = models.ForeignKey(
        to=Dictionaries, on_delete=models.CASCADE, verbose_name='Dictionary',
        related_name='indicators')
    author = models.ForeignKey(to="User", on_delete=models.SET_NULL, null=True, verbose_name='Author')

    objects = IndicatorsManager()

    def __str__(self):
        return self.short_name.get("ru", "No name")

    class Meta:
        db_table = '"dct\".\"indicators"'
        verbose_name = 'DCT Indicator'
        verbose_name_plural = 'DCT Indicators'
