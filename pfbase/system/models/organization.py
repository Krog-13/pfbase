from pfbase.base_models import default_name, TimeStampedModel, AutoSortModel
from django.db import models
from django.utils.translation import gettext_lazy as _
from pfbase.system.manager import OrganizationManager


class Organization(TimeStampedModel, AutoSortModel):
    """
    Organizations
    """
    short_name = models.JSONField(verbose_name=_('Short name'), default=default_name)
    full_name = models.JSONField(verbose_name=_('Full name'), default=default_name,
                                 null=True, blank=True)
    identifier = models.CharField(max_length=128, null=True, blank=True, verbose_name=_('Identifier'))
    active = models.BooleanField(default=True, verbose_name=_('Active'))
    code = models.CharField(max_length=128, null=True, blank=True, verbose_name=_('Code'))
    type = models.ForeignKey(
        to="ListValues", on_delete=models.CASCADE,
        verbose_name=_('Organization type'))
    parent = models.ForeignKey(
        to="self", on_delete=models.CASCADE, null=True, blank=True,
        verbose_name=_('Parent organization'), related_name='children')
    objects = OrganizationManager()

    def __str__(self):
        return self.short_name.get("ru", "No name")

    class Meta:
        db_table = '"stm\".\"organization"'
        verbose_name = _("STM Organization")
        verbose_name_plural = _("STM Organizations")
