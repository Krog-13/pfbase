from django.db import models
from .elements import Elements


class Action(models.TextChoices):
    CREATED = 'create', 'Create'
    UPDATED = 'update', 'Update'
    DELETED = 'delete', 'Delete'


class ElementHistory(models.Model):
    """
    History of actions on :Elements
    """
    status = models.ForeignKey(
        to="ListValues", on_delete=models.SET_NULL, null=True, verbose_name='Status')
    stamp = models.JSONField(verbose_name='Stamp', null=True, blank=True)
    action = models.CharField(
        choices=Action.choices, max_length=6, verbose_name='Action', default=Action.CREATED)
    element = models.ForeignKey(
        to=Elements, on_delete=models.SET_NULL, null=True, verbose_name='Dictionary element',
        related_name="history")
    author = models.ForeignKey(
        to="User", on_delete=models.SET_NULL, null=True, verbose_name='Author')
    created_at = models.DateTimeField(
        auto_now_add=True, blank=True, verbose_name='Action date and time')

    def __str__(self):
        return self.status.code if self.status else f"History {self.pk}"

    class Meta:
        db_table = '"dct\".\"element_history"'
        verbose_name = 'DCT Element History'
        verbose_name_plural = 'DCT Element Histories'
