from pfbase.base_models import default_map
from django.db import models


class Organization(models.Model):
    """
    Организации
    """
    name = models.JSONField(verbose_name='Наименование организации', default=default_map)
    identifier = models.CharField(max_length=128, null=True, blank=True, verbose_name='БИН')
    address = models.CharField(max_length=128, null=True, blank=True, verbose_name='Адрес')
    created_at = models.DateTimeField(auto_now_add=True, blank=True)

    def __str__(self):
        return self.name.get("ru", "No name")

    class Meta:
        db_table = '"stm\".\"organization"'
        verbose_name = "STM Организация"
        verbose_name_plural = "STM Организации"
