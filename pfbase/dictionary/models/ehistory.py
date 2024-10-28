from django.db import models
from .elements import Elements


class Action(models.TextChoices):
    CREATED = 'create', 'Create'
    UPDATED = 'update', 'Update'
    DELETED = 'delete', 'Delete'


class ElementHistory(models.Model):
    """
    Истрория действии над :Elements
    """
    status = models.ForeignKey(
        to="ListValues", on_delete=models.SET_NULL, null=True, verbose_name='Статус')
    stamp = models.JSONField(verbose_name='Слепок', null=True, blank=True)
    action = models.CharField(
        choices=Action.choices, max_length=6, verbose_name='Действие', default=Action.CREATED)
    element = models.ForeignKey(
        to=Elements, on_delete=models.SET_NULL, null=True, verbose_name='Элемент',
        related_name="history")
    author = models.ForeignKey(
        to="User", on_delete=models.SET_NULL, null=True, verbose_name='Автор')
    created_at = models.DateTimeField(
        auto_now_add=True, blank=True, verbose_name='Дата создания')

    def __str__(self):
        return self.status.code

    class Meta:
        db_table = '"dct\".\"element_history"'
        verbose_name = 'DCT История элемента'
        verbose_name_plural = 'DCT История элементов'
