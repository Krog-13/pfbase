from pfbase.base_models import IndicatorBase, CommonManager
from pfbase import config
from django.db import models
from .dictionaries import Dictionaries


class DctIndicators(IndicatorBase):
    """
    Показатели :Dictionaries
    """
    dictionary = models.ForeignKey(
        to=Dictionaries, on_delete=models.CASCADE, verbose_name='Справочник',
        related_name='indicators')
    author = models.ForeignKey(to="User", on_delete=models.SET_NULL, null=True, verbose_name='Автор')
    created_at = models.DateTimeField(auto_now_add=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    objects = CommonManager()

    def __str__(self):
        return self.short_name.get("ru", "No name")

    class Meta:
        db_table = '"dct\".\"indicators"'
        verbose_name = 'DCT Индикатор'
        verbose_name_plural = 'DCT Индикаторы'

    def save(self, *args, **kwargs):
        """Автоматическое заполнение сортировки"""
        if not self.pk:  # If the object is being created (not updated)
            # Get the maximum value of index_sort from existing records
            max_sort = DctIndicators.objects.aggregate(models.Max('index_sort'))['index_sort__max']
            # If max_sort is None (meaning there are no records), start at 0
            if max_sort is None:
                max_sort = config.START_STEP
            self.index_sort = max_sort + config.STEP_SORT
        super().save(*args, **kwargs)
