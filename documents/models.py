from IEF.base_model import CategoryBase, IndicatorBase, ParameterBase, IndicatorValueBase, SoftDelete
from users.models import User
from django.db import models
import json


class Category(CategoryBase):
    """
    Category for documents
    """
    class Meta:
        db_table = '"dcm\".\"categories"'
        verbose_name = 'Категорию документа'
        verbose_name_plural = 'Категории документов'


class ABCDocument(models.Model):
    """
    Abstraction Documents
    """
    dcm_name = models.JSONField(verbose_name='Наименование')
    description = models.TextField(
        null=True, blank=True, verbose_name='Описание')
    code = models.CharField(
        max_length=128, verbose_name='Код', unique=True)
    category = models.ForeignKey(
        Category, null=True, blank=True, on_delete=models.SET_NULL,
        verbose_name='Категория документа')
    author = models.ForeignKey(
        to=User, on_delete=models.CASCADE, verbose_name='Автор')

    def __str__(self):
        return self.dcm_name.get("short_name", self.code)

    class Meta:
        db_table = '"dcm\".\"abc_document"'
        verbose_name = 'Документ'
        verbose_name_plural = 'Документы'

    def save(self, *args, **kwargs):
        if self.full_name or self.part_name:
            self.dcm_name = {"full_name": self.full_name, "short_name": self.part_name}
        super().save(*args, **kwargs)


class IndicatorParameter(ParameterBase):
    """
    Default parameters for indicators
    """
    class Meta:
        db_table = '"dcm\".\"idc_parameter"'
        verbose_name = 'Параметр'
        verbose_name_plural = 'Параметры'


class Indicator(IndicatorBase):
    """
    Indicator for documents
    """
    custom_rule = models.JSONField(verbose_name='Правило', null=True, blank=True)
    abc_document = models.ForeignKey(
        to=ABCDocument, on_delete=models.CASCADE, verbose_name='Документ',
        related_name='indicator')
    reference = models.PositiveIntegerField(
        null=True, blank=True, verbose_name='Внешний ключ')
    parameters = models.ManyToManyField(
        IndicatorParameter, blank=True, verbose_name='Параметры')

    class Meta:
        db_table = '"dcm\".\"indicator"'
        verbose_name = 'Индикатор'
        verbose_name_plural = 'Индикаторы'

    def __str__(self):
        return self.short_name.get("ru")

    def save(self, *args, **kwargs):
        if not self.pk:
            max_sort = Indicator.objects.aggregate(models.Max('index_sort'))['index_sort__max']
            if max_sort is None:
                max_sort = 0
            self.index_sort = max_sort + 5
        super().save(*args, **kwargs)


class Record(SoftDelete):
    """
    Records
    """
    short_name = models.JSONField(verbose_name='Краткое наименование')
    created_at = models.DateTimeField(auto_now_add=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True)
    author = models.ForeignKey(
        to=User, on_delete=models.CASCADE, verbose_name='Автор')
    abc_document = models.ForeignKey(
        to=ABCDocument, on_delete=models.SET_NULL, null=True,
        verbose_name='Документ')
    parent = models.ForeignKey(
        "self", null=True, blank=True, related_name="children", on_delete=models.CASCADE,
        verbose_name='Родительский элемент')

    def __str__(self):
        return self.short_name.get("ru")

    class Meta:
        db_table = '"dcm\".\"record"'
        verbose_name = 'Запись документа'
        verbose_name_plural = 'Записи документов'


class RecordIndicatorValue(IndicatorValueBase):
    """
    Record-Indicator Value
    """
    value_text = models.TextField(
        null=True, blank=True, verbose_name='Текст')
    value_datetime = models.DateTimeField(
        null=True, blank=True, verbose_name='Дата и время')
    value_reference = models.PositiveIntegerField(
        null=True, blank=True, verbose_name='Внешний ключ')
    record = models.ForeignKey(
        to=Record, on_delete=models.CASCADE, verbose_name='Запсиь',
        related_name="record_value")
    indicator = models.ForeignKey(
        to=Indicator, on_delete=models.CASCADE, verbose_name='Показатель',
        related_name="indicator_value")

    class Meta:
        db_table = '"dcm\".\"indicator_value"'
        verbose_name = 'Значение поля'
        verbose_name_plural = 'Значения полей'

    def __str__(self):
        return self.value_str or self.value_text or self.value_datetime or str(self.value_int)

    @staticmethod
    def json_file_data(filename, file_id):
        file_data = {"filename": filename, "file_id": file_id}
        return json.dumps(file_data)

    def save(self, *args, **kwargs):
        if not self.pk:
            max_sort = RecordIndicatorValue.objects.aggregate(models.Max('index_sort'))['index_sort__max']
            if max_sort is None:
                max_sort = 0
            self.index_sort = max_sort + 5
        super().save(*args, **kwargs)


class Status(models.TextChoices):
    """Enum status"""
    CREATED = 'CREATED', 'Создан'
    SIGNED = 'SIGNED',  'Подписан'
    CANCELED = 'CANCELED', 'Отменен'


class RecordHistory(models.Model):
    """History of Record"""
    status = models.CharField(
        max_length=28,
        choices=Status.choices,
        default=Status.CREATED,
        verbose_name='Статус')
    status_comment = models.TextField(
        max_length=312, null=True, blank=True, verbose_name='Комментарий')
    stage = models.CharField(max_length=128, null=True, blank=True, verbose_name='Этап')
    signature = models.BooleanField(null=True, blank=True, verbose_name='Подписание')
    sign_stamp = models.TextField(verbose_name='Ключ верификации', null=True, blank=True)
    stamp = models.JSONField(verbose_name='Слепок', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True)
    author = models.ForeignKey(
        to=User, on_delete=models.CASCADE, verbose_name='Автор')
    record = models.ForeignKey(
        to=Record, on_delete=models.SET_NULL, null=True,
        verbose_name='Журнал документа', related_name="record_history")

    class Meta:
        db_table = '"dcm\".\"record_history"'
        verbose_name = 'История записи'
        verbose_name_plural = 'Истории записей'
