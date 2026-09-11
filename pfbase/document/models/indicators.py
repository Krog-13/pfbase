from pfbase.base_models import IndicatorBase
from pfbase.document.manager import DcmIndicatorsManager
from .documents import Documents
from django.db import models


class DcmIndicators(IndicatorBase):
    """
    Indicators for :Documents
    """
    document = models.ForeignKey(
        to=Documents, on_delete=models.CASCADE, verbose_name='Document',
        related_name='indicators')
    author = models.ForeignKey(to="User", on_delete=models.SET_NULL, null=True, verbose_name='Author',
                               related_name="indicators")
    calc_rule = models.JSONField(verbose_name='Calculation rule', null=True, blank=True)
    objects = DcmIndicatorsManager()

    def __str__(self):
        return self.short_name.get("ru", "No name")

    class Meta:
        db_table = '"dcm\".\"indicators"'
        verbose_name = 'DCM Indicator'
        verbose_name_plural = 'DCM Indicators'
