from django.db import models
from .elements import Elements


class ElementHistory(models.Model):
    """
    Истрория действии над :Elements
    """
    stamp = models.JSONField(verbose_name='Слепок', null=True, blank=True)
    action = models.CharField(max_length=128, null=True, blank=True, verbose_name='Действие')
    element = models.ForeignKey(
        to=Elements, on_delete=models.SET_NULL, null=True, verbose_name='Элемент',
        related_name="history")
    author = models.ForeignKey(
        to="User", on_delete=models.SET_NULL, null=True, verbose_name='Автор')
    created_at = models.DateTimeField(
        auto_now_add=True, blank=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(
        auto_now=True, blank=True, verbose_name='Дата обновления')
    status_enum = models.ForeignKey(
        to="ListValues", on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Статус действия')

    def __str__(self):
        return self.action

    class Meta:
        db_table = '"dct\".\"element_history"'
        verbose_name = 'DCT История элемента'
        verbose_name_plural = 'DCT История элементов'
