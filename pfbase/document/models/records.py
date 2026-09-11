from pfbase.base_models import SoftDelete, TimeStampedModel
from .documents import Documents
from django.db import models
from ..manager import RecordsManager


class Records(SoftDelete, TimeStampedModel):
    """
    Records for :Documents
    """
    number = models.CharField(verbose_name="Number", max_length=255)
    date = models.DateTimeField(verbose_name="Date")
    active = models.BooleanField(default=True, verbose_name="Active")
    document = models.ForeignKey(
        to=Documents, on_delete=models.SET_NULL, null=True,
        verbose_name='Document')
    parent = models.ForeignKey(
        "self", null=True, blank=True, related_name="children", on_delete=models.CASCADE,
        verbose_name='Parent record')
    author = models.ForeignKey(
        to="User", on_delete=models.CASCADE, verbose_name='Author')
    organization = models.ForeignKey(
        to="Organization", on_delete=models.SET_NULL, blank=True, null=True,
        verbose_name='Organization', related_name="records")

    objects = RecordsManager()

    def __str__(self):
        return f"Record #{self.pk}"

    def admin_document(self):
        if not self.document:
            return f"Record #{self.pk}"

        return (
            f"{self.document.name.get('ru', 'No name')} "
            f"№{self.number} от {self.date:%d.%m.%Y}"
        )

    class Meta:
        db_table = '"dcm\".\"records"'
        verbose_name = 'DCM Document Record'
        verbose_name_plural = 'DCM Document Records'
