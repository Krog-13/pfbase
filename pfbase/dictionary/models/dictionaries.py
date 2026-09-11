from pfbase.base_models import default_name, CommonManager, TimeStampedModel
from django.db import models


class DictionaryType(models.TextChoices):
    MAIN = 'main', 'Main'
    SUB = 'sub', 'Sub'


class Dictionaries(TimeStampedModel):
    """
    Dictionary abstractions
    """
    name = models.JSONField(verbose_name='Name', default=default_name)
    description = models.JSONField(
        null=True, blank=True, verbose_name='Description', default=default_name)
    code = models.CharField(
        max_length=128, verbose_name='Code', unique=True)
    author = models.ForeignKey(
        to="User", on_delete=models.SET_NULL, null=True, verbose_name='Author')
    active = models.BooleanField(
        default=True, verbose_name='Active')
    parent = models.ForeignKey(
        "self", null=True, blank=True, related_name="children",
        on_delete=models.CASCADE, verbose_name='Parent abstraction')
    organization = models.ForeignKey(
        to="Organization", on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Organization')
    type = models.CharField(
        choices=DictionaryType.choices, max_length=4,
        verbose_name='Abstraction type', default=DictionaryType.MAIN)

    objects = CommonManager()

    def __str__(self):
        return self.name.get("ru", "No name")

    class Meta:
        db_table = '"dct\".\"dictionaries"'
        verbose_name = 'DCT Dictionary'
        verbose_name_plural = 'DCT Dictionaries'
