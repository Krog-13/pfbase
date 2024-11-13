from pfbase.base_models import default_name, CommonManager
from django.db import models


class ListValues(models.Model):
    """
    Список значений
    """
    list = models.CharField(max_length=128, verbose_name='Список')
    code = models.CharField(max_length=128, verbose_name='Код значения')
    short_name = models.JSONField(
        verbose_name='Краткое наименование', default=default_name)
    full_name = models.JSONField(
        verbose_name='Полное наименование', null=True, blank=True, default=default_name)
    active = models.BooleanField(default=True, verbose_name='Активный')
    author = models.ForeignKey(
        to="User", on_delete=models.CASCADE, verbose_name='Автор', related_name="list_values")
    index_sort = models.PositiveIntegerField(blank=True, verbose_name='Индекс сортировки', null=True, default=0)
    created_at = models.DateTimeField(auto_now_add=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    objects = CommonManager()

    def __str__(self):
        return self.list + "." + self.code

    class Meta:
        db_table = '"stm\".\"list_values"'
        verbose_name = 'STM Список значений'
        verbose_name_plural = 'STM Списки значений'
