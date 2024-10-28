from pfbase.base_models import IndicatorBase, CommonManager
from .documents import Documents
from django.db import models
from pfbase import config


class DcmIndicators(IndicatorBase):
    """
    Показатели :Documents
    """
    custom_rule = models.JSONField(verbose_name='Правило', null=True, blank=True)
    document = models.ForeignKey(
        to=Documents, on_delete=models.CASCADE, verbose_name='Документ',
        related_name='indicators')
    reference = models.PositiveIntegerField(
        null=True, blank=True, verbose_name='Внешний ключ')
    author = models.ForeignKey(to="User", on_delete=models.SET_NULL, null=True, verbose_name='Автор',
                               related_name="indicators")
    objects = CommonManager()

    def __str__(self):
        return self.name.get("ru", "No name")

    class Meta:
        db_table = '"dcm\".\"indicators"'
        verbose_name = 'DCM Индикатор'
        verbose_name_plural = 'DCM Индикаторы'

    def save(self, *args, **kwargs):
        """Автоматическое заполнение сортировки"""
        if not self.pk:
            max_sort = DcmIndicators.objects.aggregate(models.Max('index_sort'))['index_sort__max']
            if max_sort is None:
                max_sort = 0
            self.index_sort = max_sort + config.STEP_SORT
        super().save(*args, **kwargs)
