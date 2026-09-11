from django.db import models
from django.utils.translation import gettext_lazy as _
from pfbase.base_models import TimeStampedModel


class Action(models.TextChoices):
    CREATED = 'create', _('Create')
    UPDATED = 'update', _('Update')
    DELETED = 'delete', _('Delete')


class SystemHistory(TimeStampedModel):
    """
    History of system actions
    """
    action = models.CharField(
        max_length=10, choices=Action.choices, verbose_name=_('Action'), default=Action.CREATED)
    stamp = models.JSONField(verbose_name=_('Stamp'), null=True, blank=True)
    author = models.ForeignKey(to="User", on_delete=models.CASCADE, verbose_name=_('Author'))

    class Meta:
        db_table = '"stm\".\"system_history"'
        verbose_name = _('STM System History')
        verbose_name_plural = _('STM System Histories')