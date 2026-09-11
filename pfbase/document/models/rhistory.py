from django.db import models
from .records import Records


class Action(models.TextChoices):
    CREATED = 'create', 'Create'
    UPDATED = 'update', 'Update'
    DELETED = 'delete', 'Delete'


class RecordHistory(models.Model):
    """
    History of actions on :Records
    """
    status = models.ForeignKey(
        to="ListValues", on_delete=models.SET_NULL, null=True, verbose_name='Status')
    action = models.CharField(
        max_length=10, choices=Action.choices, verbose_name='Action', default=Action.CREATED)
    comment = models.TextField(verbose_name='Comment', null=True, blank=True, max_length=900)
    stamp = models.JSONField(verbose_name='Stamp', null=True, blank=True)
    sign_stamp = models.TextField(verbose_name='Sign stamp', null=True, blank=True)
    record = models.ForeignKey(
        to=Records, on_delete=models.SET_NULL, null=True,
        verbose_name='Document record', related_name="history")
    author = models.ForeignKey(
        to="User", on_delete=models.CASCADE, verbose_name='Author')
    created_at = models.DateTimeField(auto_now_add=True, blank=True,
                                      verbose_name='Action date and time')

    def __str__(self):
        return self.status.code if self.status else f"History {self.pk}"

    class Meta:
        db_table = '"dcm\".\"record_history"'
        verbose_name = 'DCM Record History'
        verbose_name_plural = 'DCM Record Histories'
