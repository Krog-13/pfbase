from pfbase.base_models import default_map, CommonManager
from django.db import models


class DictionaryType(models.TextChoices):
    MAIN = 'main', 'Main'
    SUB = 'sub', 'Sub'


class Dictionaries(models.Model):
    """
    Абстракция справочника
    """
    name = models.JSONField(verbose_name='Наименование', default=default_map)
    description = models.JSONField(
        null=True, blank=True, verbose_name='Описание', default=default_map)
    code = models.CharField(
        max_length=128, verbose_name='Код', unique=True)
    author = models.ForeignKey(
        to="User", on_delete=models.SET_NULL, null=True, verbose_name='Автор')
    active = models.BooleanField(
        default=True, verbose_name='Активный')
    parent = models.ForeignKey(
        "self", null=True, blank=True, related_name="children",
        on_delete=models.CASCADE, verbose_name='Родительский элемент')
    organization = models.ForeignKey(
        to="Organization", on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Организация')
    type = models.CharField(
        choices=DictionaryType.choices, max_length=4,
        verbose_name='Тип', default=DictionaryType.MAIN)
    objects = CommonManager()
    created_at = models.DateTimeField(auto_now_add=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True)
    deleted_at = models.DateTimeField(null=True, blank=True)


    def __str__(self):
        return self.name.get("ru", "No name")

    class Meta:
        db_table = '"dct\".\"dictionaries"'
        verbose_name = 'DCT Справочник'
        verbose_name_plural = 'DCT Справочники'
