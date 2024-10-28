from pfbase.base_models import default_name
from django.db import models


class Organization(models.Model):
    """
    Организации
    """
    short_name = models.JSONField(verbose_name='Краткое наименование', default=default_name)
    full_name = models.JSONField(verbose_name='Полное наименование', default=default_name,
                                 null=True, blank=True)
    identifier = models.CharField(max_length=128, null=True, blank=True, verbose_name='Идентификатор')
    active = models.BooleanField(default=True, verbose_name='Активный')
    code = models.CharField(max_length=128, null=True, blank=True, verbose_name='Код')
    type = models.ForeignKey(
        to="ListValues", on_delete=models.CASCADE,
        verbose_name='Тип организации')
    parent = models.ForeignKey(
        to="self", on_delete=models.CASCADE, null=True, blank=True,
        verbose_name='Родительская организация', related_name='children')
    created_at = models.DateTimeField(auto_now_add=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.short_name.get("ru", "No name")

    class Meta:
        db_table = '"stm\".\"organization"'
        verbose_name = "STM Организация"
        verbose_name_plural = "STM Организации"
