from django.db import models
from enum import Enum
from pfbase.config import default_name


class NotificationType(Enum):
    INFO = 'info'
    WARNING = 'warning'
    REMINDER = 'reminder'
    ERROR = 'error'

    @classmethod
    def choices(cls):
        return [(tag.value, tag.name) for tag in cls]


class Notification(models.Model):
    """
    Уведомления
    """
    title = models.JSONField(verbose_name='Заголовок', default=default_name, blank=True)
    message = models.JSONField(verbose_name='Сообщение', default=default_name, blank=True)
    is_read = models.BooleanField(default=False, verbose_name='Прочитано')
    read_at = models.DateTimeField(auto_now=True, blank=True, null=True)
    type_notification = models.CharField(
        max_length=20,
        choices=NotificationType.choices(),
        default=NotificationType.INFO.value,
        verbose_name='Тип уведомления')

    created_at = models.DateTimeField(auto_now_add=True, blank=True)
    receiver_user = models.ForeignKey(
        to="User", on_delete=models.CASCADE, verbose_name='Получатель', related_name="receiver")
    sender_user = models.ForeignKey(
        to="User", on_delete=models.CASCADE, verbose_name='Отправитель', related_name='sender')
    record = models.ForeignKey(
        to="Records", on_delete=models.CASCADE, verbose_name='Запись', null=True, blank=True)
    element = models.ForeignKey(
        to="Elements", on_delete=models.CASCADE, verbose_name='Элемент', null=True, blank=True)

    class Meta:
        db_table = '"stm\".\"notification"'
        verbose_name = 'STM Уведомление'
        verbose_name_plural = 'STM Уведомления'
