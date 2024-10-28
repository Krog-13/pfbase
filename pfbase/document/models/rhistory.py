from django.db import models
from .records import Records


class RecordHistory(models.Model):
    """
    История действии над :Records
    """
    status = models.CharField(
        max_length=28,
        default="created",
        verbose_name='Статус')
    status_comment = models.TextField(
        max_length=312, null=True, blank=True, verbose_name='Комментарий')
    stage = models.CharField(max_length=128, null=True, blank=True, verbose_name='Этап')
    action = models.CharField(max_length=128, null=True, blank=True, verbose_name='Действие')
    signature = models.BooleanField(null=True, blank=True, verbose_name='Подписание')
    sign_stamp = models.TextField(verbose_name='Слепок верификации', null=True, blank=True)
    stamp = models.JSONField(verbose_name='Слепок', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True)
    author = models.ForeignKey(
        to="User", on_delete=models.CASCADE, verbose_name='Автор')
    record = models.ForeignKey(
        to=Records, on_delete=models.SET_NULL, null=True,
        verbose_name='Журнал документа', related_name="history")
    status_list = models.ForeignKey(
        to="ListValues", on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Статус действия')

    def __str__(self):
        return self.status_list.short_name.get("ru")

    class Meta:
        db_table = '"dcm\".\"record_history"'
        verbose_name = 'DCM История записи'
        verbose_name_plural = 'DCM Истории записей'
