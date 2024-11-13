from django.db import models
from .records import Records


class Action(models.TextChoices):
    CREATED = 'create', 'Create'
    UPDATED = 'update', 'Update'
    DELETED = 'delete', 'Delete'


class RecordHistory(models.Model):
    """
    История действии над :Records
    """
    status = models.ForeignKey(
        to="ListValues", on_delete=models.SET_NULL, null=True, verbose_name='Статус')
    action = models.CharField(
        max_length=10, choices=Action.choices, verbose_name='Действие', default=Action.CREATED)
    comment = models.TextField(verbose_name='Комментарий', null=True, blank=True, max_length=900)
    stamp = models.JSONField(verbose_name='Слепок', null=True, blank=True)
    sign_stamp = models.TextField(verbose_name='Слепок подписания', null=True, blank=True)
    record = models.ForeignKey(
        to=Records, on_delete=models.SET_NULL, null=True,
        verbose_name='Запись документа', related_name="history")
    author = models.ForeignKey(
        to="User", on_delete=models.CASCADE, verbose_name='Автор')
    created_at = models.DateTimeField(auto_now_add=True, blank=True,
                                      verbose_name='Дата и время действия')

    def __str__(self):
        return self.status.code

    class Meta:
        db_table = '"dcm\".\"record_history"'
        verbose_name = 'DCM История записи'
        verbose_name_plural = 'DCM Истории записей'
