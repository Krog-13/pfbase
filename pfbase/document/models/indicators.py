from pfbase.base_models import IndicatorBase, CommonManager
from pfbase import config
from .documents import Documents
from django.db import models


class DcmIndicators(IndicatorBase):
    """
    Показатели :Documents
    """
    document = models.ForeignKey(
        to=Documents, on_delete=models.CASCADE, verbose_name='Документ',
        related_name='indicators')
    author = models.ForeignKey(to="User", on_delete=models.SET_NULL, null=True, verbose_name='Автор',
                               related_name="indicators")
    calc_rule = models.JSONField(verbose_name='Правило вычисления', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    objects = CommonManager()

    def __str__(self):
        return self.short_name.get("ru", "No name")

    class Meta:
        db_table = '"dcm\".\"indicators"'
        verbose_name = 'DCM Индикатор'
        verbose_name_plural = 'DCM Индикаторы'

    def save(self, *args, **kwargs):
        """Автоматическое заполнение сортировки"""
        if not self.pk:
            max_sort = DcmIndicators.objects.aggregate(models.Max('index_sort'))['index_sort__max']
            if max_sort is None:
                max_sort = config.START_STEP
            self.index_sort = max_sort + config.STEP_SORT
        super().save(*args, **kwargs)
