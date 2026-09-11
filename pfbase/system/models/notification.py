from django.db import models
from django.utils.translation import gettext_lazy as _
from pfbase.base_models import default_name, TimeStampedModel


class NotificationType(models.TextChoices):
    INFO = 'info', _('Info')
    WARNING = 'warning', _('Warning')
    REMINDER = 'reminder', _('Reminder')
    ERROR = 'error', _('Error')


class Notification(TimeStampedModel):
    """
    Notifications
    """
    title = models.JSONField(verbose_name=_('Title'), default=default_name, blank=True)
    message = models.JSONField(verbose_name=_('Message'), default=default_name, blank=True)
    is_read = models.BooleanField(default=False, verbose_name=_('Is read'))
    read_at = models.DateTimeField(auto_now=True, blank=True, null=True, verbose_name=_('Read at'))
    type_notification = models.CharField(
        max_length=20,
        choices=NotificationType.choices,
        default=NotificationType.INFO,
        verbose_name=_('Notification type'))
    receiver_user = models.ForeignKey(
        to="User", on_delete=models.CASCADE, verbose_name=_('Receiver'), related_name="receiver")
    sender_user = models.ForeignKey(
        to="User", on_delete=models.CASCADE, verbose_name=_('Sender'), related_name='sender')
    record = models.ForeignKey(
        to="Records", on_delete=models.CASCADE, verbose_name=_('Record'), null=True, blank=True)
    element = models.ForeignKey(
        to="Elements", on_delete=models.CASCADE, verbose_name=_('Element'), null=True, blank=True)

    class Meta:
        db_table = '"stm\".\"notification"'
        verbose_name = _('STM Notification')
        verbose_name_plural = _('STM Notifications')
