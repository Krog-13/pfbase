from IEF.base_model import CategoryBase, IndicatorBase, DefaultParameterBase, IndicatorValueBase, SoftDelete
from users.models import Organization, User
from django.db import models
import json


class CategoryDocument(CategoryBase):
    """
    Категории документов
    """
    class Meta:
        db_table = '"dcm\".\"categories"'
        verbose_name = 'Категорию документа'
        verbose_name_plural = 'Категории документов'


class ABCDocument(models.Model):
    """
    Abstraction Documents
    """
    naming = models.JSONField(
        max_length=255, verbose_name='Наименование', null=True, blank=True)
    description = models.TextField(
        null=True, blank=True, verbose_name='Описание')
    abc_code = models.CharField(max_length=128, verbose_name='Код', null=True, blank=True)
    organizations = models.ManyToManyField(
        to=Organization, blank=True, verbose_name='Организация')
    category_document = models.ForeignKey(
        CategoryDocument, null=True, blank=True, on_delete=models.SET_NULL, verbose_name='Категория документа')
    author = models.ForeignKey(
        to=User, on_delete=models.CASCADE, verbose_name='Автор')

    def __str__(self):
        return self.naming["short_name"]

    class Meta:
        db_table = '"dcm\".\"abc_documents"'
        verbose_name = 'Документ'
        verbose_name_plural = 'Документы'

    def save(self, *args, **kwargs):
        if self.full_name or self.part_name:
            self.naming = {"full_name": self.full_name, "short_name": self.part_name}
        super().save(*args, **kwargs)


class JournalDocument(SoftDelete):
    """
    Elements
    """
    short_name = models.CharField(
        max_length=128, unique=False, verbose_name='Наименование')
    code = models.CharField(max_length=128, verbose_name='Код', null=True, blank=True)
    doc_number = models.CharField(max_length=216, verbose_name='Номер документа', null=True, blank=True)
    date_time = models.DateTimeField(verbose_name="Дата создания", null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True)
    author = models.ForeignKey(
        to=User, on_delete=models.CASCADE, verbose_name='Автор')
    abc_document = models.ForeignKey(to=ABCDocument, null=True, blank=True, on_delete=models.SET_NULL, verbose_name='Документ')
    parent = models.ForeignKey("self", null=True, blank=True, related_name="children", on_delete=models.SET_NULL,
                               verbose_name='Родительский элемент')

    def __str__(self):
        return self.short_name

    class Meta:
        db_table = '"dcm\".\"journal"'
        verbose_name = 'Журнал документа'
        verbose_name_plural = 'Журнал Документов'


class JournalStatus(models.TextChoices):
    """Enum status"""
    CREATED = 'CREATED', 'Создан'
    REVIEW = 'REVIEW', 'На согласовании подрядчика'
    AVERMENT = 'AVERMENT', 'На утверждении подрядчика'
    AVERMENT_ABP = 'AVERMENT_ABP', 'На утверждении АБП'
    REVIEW_ROOT = 'REVIEW_ROOT', 'На согласовании заказчика'
    AVERMENT_ROOT = 'AVERMENT_ROOT', 'На утверждении заказчика'
    SIGNED = 'SIGNED',  'Подписан'
    CANCELED = 'CANCELED', 'Отменен'


class HistoryJournal(models.Model):
    """History of Journal"""
    journal_status = models.CharField(max_length=28,
                                      choices=JournalStatus.choices,
                                      default=JournalStatus.CREATED,
                                      verbose_name='Статус')
    status_comment = models.TextField(max_length=312, null=True, blank=True, verbose_name='Комментарий')
    stage = models.CharField(max_length=5, null=True, blank=True, verbose_name='Этап')
    signature = models.BooleanField(null=True, blank=True, default=False, verbose_name='Подписание')
    created_at = models.DateTimeField(auto_now_add=True, blank=True)
    data_stamp = models.JSONField(verbose_name='Слепок', null=True, blank=True)
    data_sign = models.JSONField(verbose_name='Подписание ЭЦП', null=True, blank=True)
    author = models.ForeignKey(
        to=User, on_delete=models.CASCADE, verbose_name='Автор')
    journal_document = models.ForeignKey(to=JournalDocument, null=True, blank=True, on_delete=models.SET_NULL,
                                         verbose_name='Журнал документа', related_name="history_status")

    class Meta:
        db_table = '"dcm\".\"history_journal"'
        verbose_name = 'История Журнала'
        verbose_name_plural = 'Истории Журнала'


class IndicatorParameter(DefaultParameterBase):
    """
    Параметры для поля
    """
    class Meta:
        db_table = '"dcm\".\"default_parameters"'
        verbose_name = 'Параметр'
        verbose_name_plural = 'Параметры'


class DocumentField(IndicatorBase):
    """
    Поля
    """
    idc_code = models.CharField(max_length=128, verbose_name='Код', null=True, blank=True)
    custom_rule = models.JSONField(max_length=255, verbose_name='Правило', null=True, blank=True)
    document = models.ForeignKey(
        to=ABCDocument, on_delete=models.CASCADE, verbose_name='Документ', null=True,
        related_name='document_indicators')
    reference = models.PositiveIntegerField(null=True, blank=True, verbose_name="Foreign Key")
    parameters = models.ManyToManyField(
        IndicatorParameter, blank=True, verbose_name='Параметры')

    class Meta:
        db_table = '"dcm\".\"indicator"'
        verbose_name = 'Поле'
        verbose_name_plural = 'Поля'


class FieldValue(IndicatorValueBase):
    """
    Значения полей
    """
    journal_document = models.ForeignKey(
        to=JournalDocument, on_delete=models.CASCADE, verbose_name='Журнал документа',
        related_name="field_value")
    indicator = models.ForeignKey(
        to=DocumentField, on_delete=models.CASCADE, verbose_name='Показатель',
        related_name="indicator_doc")

    class Meta:
        db_table = '"dcm\".\"indicator_values"'
        verbose_name = 'Значение поля'
        verbose_name_plural = 'Значения полей'

    def __str__(self):
        return self.indicator_value if self.indicator_value else self.indicator.short_name

    @staticmethod
    def json_file_data(filename, file_id):
        file_data = {"filename": filename, "file_id": file_id}
        return json.dumps(file_data)
