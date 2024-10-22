from pfbase.base_models import SoftDelete
from .documents import Documents
from django.db import models


class Records(SoftDelete):
    """
    Запсиси :Documents
    """
    number = models.CharField(verbose_name="Номер", max_length=255)
    date = models.DateField(verbose_name="Дата")
    created_at = models.DateTimeField(auto_now_add=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True)
    active = models.BooleanField(default=True, verbose_name="Активный")
    document = models.ForeignKey(
        to=Documents, on_delete=models.SET_NULL, null=True,
        verbose_name='Документ')
    parent = models.ForeignKey(
        "self", null=True, blank=True, related_name="children", on_delete=models.CASCADE,
        verbose_name='Родительский элемент')
    author = models.ForeignKey(
        to="User", on_delete=models.CASCADE, verbose_name='Автор')
    organization = models.ForeignKey(
        to="organization", on_delete=models.SET_NULL, blank=True, null=True,
        verbose_name='Организация', related_name="records")

    def __str__(self):
        return self.number

    class Meta:
        db_table = '"dcm\".\"records"'
        verbose_name = 'DCM Запись документа'
        verbose_name_plural = 'DCM Записи документов'

    def create_iv(self, user, data):
        """
        Создание записи
        """
        serializer = RecordPostSerializer(data=data, context={'user': user})
        if serializer.is_valid():
            serializer.save()
            return self
