from pfbase.base_models import default_map, CommonManager
from django.db import models


class ListValues(models.Model):
    """
    Словарь перечислении
    """
    list = models.CharField(max_length=128, verbose_name='Код списка')
    code = models.CharField(max_length=128, verbose_name='Код элемента')
    short_name = models.JSONField(
        verbose_name='Краткое наименование', default=default_map)
    full_name = models.JSONField(
        verbose_name='Полное наименование', null=True, blank=True, default=default_map)
    active = models.BooleanField(default=True, verbose_name='Активный')
    author = models.ForeignKey(
        to="User", on_delete=models.CASCADE, verbose_name='Автор', related_name="enum")
    objects = CommonManager()

    def __str__(self):
        return self.list

    class Meta:
        db_table = '"stm\".\"list_values"'
        verbose_name = 'STM Перечисление'
        verbose_name_plural = 'STM Перечисления'
