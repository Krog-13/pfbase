from django.db import models
from enum import Enum


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
    title = models.CharField(max_length=128, verbose_name='Заголовок')
    message = models.TextField(verbose_name='Сообщение')
    is_read = models.BooleanField(default=False, verbose_name='Прочитано')
    read_at = models.DateTimeField(auto_now=True, blank=True, null=True)
    type_notification = models.CharField(
        max_length=20,
        choices=NotificationType.choices(),
        default=NotificationType.INFO.value,
        verbose_name='Тип уведомления')

    created_at = models.DateTimeField(auto_now_add=True, blank=True)
    user_receiver = models.ForeignKey(
        to="User", on_delete=models.CASCADE, verbose_name='Получатель', related_name="receiver")
    user_sender = models.ForeignKey(
        to="User", on_delete=models.CASCADE, verbose_name='Отправитель', related_name='sender')
    record = models.ForeignKey(
        to="Records", on_delete=models.CASCADE, verbose_name='Запись', null=True, blank=True)
    element = models.ForeignKey(
        to="Elements", on_delete=models.CASCADE, verbose_name='Элемент', null=True, blank=True)

    class Meta:
        db_table = '"stm\".\"notification"'
        verbose_name = 'STM Уведомление'
        verbose_name_plural = 'STM Уведомления'
