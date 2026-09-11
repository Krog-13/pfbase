from pfbase.base_models import default_name, TimeStampedModel, AutoSortModel
from .dictionaries import Dictionaries
from django.db import models
from ..manager import ElementManager


class Elements(TimeStampedModel, AutoSortModel):
    """
    Elements for :Dictionaries
    """
    short_name = models.JSONField(
        verbose_name='Short name', default=default_name)
    full_name = models.JSONField(
        verbose_name='Full name', null=True, blank=True, default=default_name)
    code = models.CharField(
        max_length=128, verbose_name='Code', unique=False, null=True, blank=True)
    dictionary = models.ForeignKey(
        to=Dictionaries, on_delete=models.SET_NULL, null=True,
        verbose_name='Dictionary', related_name="elements")
    parent = models.ForeignKey(
        "self", null=True, blank=True, related_name="children",
        on_delete=models.CASCADE, verbose_name='Parent element')
    active = models.BooleanField(
        default=True, verbose_name='Active')
    author = models.ForeignKey(
        to="User", on_delete=models.SET_NULL, null=True, verbose_name='Author', related_name="elements")
    organization = models.ForeignKey(
        to="Organization", on_delete=models.SET_NULL, blank=True, null=True,
        verbose_name='Organization', related_name="elements")

    objects = ElementManager()

    def __str__(self):
        return self.short_name.get("ru", "No name")

    class Meta:
        db_table = '"dct\".\"elements"'
        verbose_name = 'DCT Element'
        verbose_name_plural = 'DCT Elements'
