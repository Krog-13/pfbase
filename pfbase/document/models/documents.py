from pfbase.base_models import default_map, CommonManager
from django.db import models


class Documents(models.Model):
    """
    Абстракция документа
    """
    name = models.JSONField(
        verbose_name='Наименование', default=default_map)
    description = models.JSONField(
        null=True, blank=True, verbose_name='Описание', default=default_map)
    code = models.CharField(
        max_length=128, verbose_name='Код', unique=True)
    author = models.ForeignKey(
        to="User", on_delete=models.CASCADE, verbose_name='Автор')
    parent = models.ForeignKey(
        "self", null=True, blank=True, related_name="children",
        on_delete=models.CASCADE, verbose_name='Родительский элемент')
    organization = models.ForeignKey(
        to="Organization", on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Организация')
    objects = CommonManager()

    def __str__(self):
        return self.name.get("ru", "No name")

    class Meta:
        db_table = '"dcm\".\"documents"'
        verbose_name = 'DCM Документ'
        verbose_name_plural = 'DCM Документы'
