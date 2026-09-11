from pfbase.base_models import default_name, CommonManager, TimeStampedModel, AutoSortModel
from django.db import models
from django.utils.translation import gettext_lazy as _


class ListValues(TimeStampedModel, AutoSortModel):
    """
    List of values
    """
    list = models.CharField(max_length=128, verbose_name=_('List'))
    code = models.CharField(max_length=128, verbose_name=_('Code'))
    short_name = models.JSONField(
        verbose_name=_('Short name'), default=default_name)
    full_name = models.JSONField(
        verbose_name=_('Full name'), null=True, blank=True, default=default_name)
    active = models.BooleanField(default=True, verbose_name=_('Active'))
    author = models.ForeignKey(
        to="User", on_delete=models.CASCADE, verbose_name=_('Author'), related_name="list_values")

    objects = CommonManager()

    def __str__(self):
        return f"{self.list}.{self.code}"

    class Meta:
        db_table = '"stm\".\"list_values"'
        verbose_name = _('STM List Value')
        verbose_name_plural = _('STM List Values')
