from pfbase.base_models import default_name, CommonManager
from .dictionaries import Dictionaries
from django.db import models
from ..manager import ElementManager

class Elements(models.Model):
    """
    Элементы :Dictionary
    """
    short_name = models.JSONField(
        verbose_name='Краткое наименование', default=default_name)
    full_name = models.JSONField(
        verbose_name='Полное наименование', null=True, blank=True, default=default_name)
    code = models.CharField(
        max_length=128, verbose_name='Код', unique=False, null=True, blank=True)
    dictionary = models.ForeignKey(
        to=Dictionaries, on_delete=models.SET_NULL, null=True,
        verbose_name='Справочник', related_name="elements")
    parent = models.ForeignKey(
        "self", null=True, blank=True, related_name="children",
        on_delete=models.CASCADE, verbose_name='Родительский элемент')
    active = models.BooleanField(
        default=True, verbose_name='Активный')
    author = models.ForeignKey(
        to="User", on_delete=models.SET_NULL, null=True, verbose_name='Автор', related_name="elements")
    organization = models.ForeignKey(
        to="Organization", on_delete=models.SET_NULL, blank=True, null=True,
        verbose_name='Организация', related_name="elements")
    created_at = models.DateTimeField(auto_now_add=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    objects = ElementManager()

    def __str__(self):
        return self.short_name.get("ru", "No name")

    class Meta:
        db_table = '"dct\".\"elements"'
        verbose_name = 'DCT Элемент'
        verbose_name_plural = 'DCT Элементы'
