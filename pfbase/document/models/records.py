from pfbase.base_models import SoftDelete
from .documents import Documents
from django.db import models
from ..manager import RecordsManager

# ToDo: размножить SoftDelete в каждом приложении
class Records(SoftDelete):
    """
    Запсиси :Documents
    """
    number = models.CharField(verbose_name="Номер", max_length=255)
    date = models.DateTimeField(verbose_name="Дата")
    active = models.BooleanField(default=True, verbose_name="Активный")
    document = models.ForeignKey(
        to=Documents, on_delete=models.SET_NULL, null=True,
        verbose_name='Документ')
    parent = models.ForeignKey(
        "self", null=True, blank=True, related_name="children", on_delete=models.CASCADE,
        verbose_name='Родительская запись')
    author = models.ForeignKey(
        to="User", on_delete=models.CASCADE, verbose_name='Автор')
    organization = models.ForeignKey(
        to="Organization", on_delete=models.SET_NULL, blank=True, null=True,
        verbose_name='Организация', related_name="records")
    created_at = models.DateTimeField(auto_now_add=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
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
        verbose_name = 'DCM Запись документа'
        verbose_name_plural = 'DCM Записи документов'
