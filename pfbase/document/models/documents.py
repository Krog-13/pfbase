from pfbase.base_models import default_name, CommonManager
from django.db import models


class DocumentType(models.TextChoices):
    MAIN = 'main', 'Main'
    SUB = 'sub', 'Sub'


class Documents(models.Model):
    """
    Абстракции документов
    """
    name = models.JSONField(
        verbose_name='Наименование', default=default_name)
    description = models.JSONField(
        null=True, blank=True, verbose_name='Описание', default=default_name)
    code = models.CharField(
        max_length=128, verbose_name='Код', unique=True)
    author = models.ForeignKey(
        to="User", on_delete=models.CASCADE, verbose_name='Автор')
    parent = models.ForeignKey(
        "self", null=True, blank=True, related_name="children",
        on_delete=models.CASCADE, verbose_name='Родительская абстракция')
    organization = models.ForeignKey(
        to="Organization", on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Организация')
    type = models.CharField(
        choices=DocumentType.choices, max_length=4,
        verbose_name='Тип абстракции', default=DocumentType.MAIN)
    index_sort = models.PositiveIntegerField(blank=True, null=True, verbose_name='Индекс сортировки')
    created_at = models.DateTimeField(auto_now_add=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    objects = CommonManager()

    def __str__(self):
        return self.name.get("ru", "No name")

    class Meta:
        db_table = '"dcm\".\"documents"'
        verbose_name = 'DCM Документ'
        verbose_name_plural = 'DCM Документы'
