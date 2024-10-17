"""
Main models by Pertro Flow project
consist of schemas:
:dct
:dcm
:sys
"""
from .base_models import IndicatorBase, IndicatorValueBase, default_map, ParameterBase, SoftDelete
from django.contrib.auth.models import AbstractUser
from django.db import models
from enum import Enum
import json


# Models for Dictionaries schemas
class ABCDictionary(models.Model):
    """
    Абстракция справочника
    """
    name = models.JSONField(verbose_name='Наименование', default=default_map)
    description = models.JSONField(
        null=True, blank=True, verbose_name='Описание', default=default_map)
    code = models.CharField(
        max_length=128, verbose_name='Код', unique=True)
    author = models.ForeignKey(
        to="User", on_delete=models.SET_NULL, null=True, verbose_name='Автор')
    active = models.BooleanField(
        default=True, verbose_name='Активный')
    parent = models.ForeignKey(
        "self", null=True, blank=True, related_name="children",
        on_delete=models.CASCADE, verbose_name='Родительский элемент')

    def __str__(self):
        return self.name.get("ru", "No name")

    class Meta:
        db_table = '"dct\".\"abc_dictionary"'
        verbose_name = 'DCT Справочник'
        verbose_name_plural = 'DCT Справочники'


class DctIndicator(IndicatorBase):
    """
    Показатели :ABCDictionary
    """
    abc_dictionary = models.ForeignKey(
        to=ABCDictionary, on_delete=models.CASCADE, verbose_name='Справочник',
        related_name='indicator')
    reference = models.ForeignKey(
        to=ABCDictionary, on_delete=models.CASCADE, verbose_name='Внешний ключ',
        null=True, blank=True, related_name='reference')
    author = models.ForeignKey(to="User", on_delete=models.SET_NULL, null=True, verbose_name='Автор',
                               related_name="indicator_author")

    def __str__(self):
        return self.name.get("ru", "No name")

    class Meta:
        db_table = '"dct\".\"dct_indicator"'
        verbose_name = 'DCT Индикатор'
        verbose_name_plural = 'DCT Индикаторы'

    def save(self, *args, **kwargs):
        """
        Счетчик сортировки +5
        """
        if not self.pk:  # If the object is being created (not updated)
            # Get the maximum value of index_sort from existing records
            max_sort = DctIndicator.objects.aggregate(models.Max('index_sort'))['index_sort__max']
            # If max_sort is None (meaning there are no records), start at 0
            if max_sort is None:
                max_sort = 0
            self.index_sort = max_sort + 5
        super().save(*args, **kwargs)


class Element(models.Model):
    """
    Элементы :ABCDictionary
    """
    short_name = models.JSONField(
        verbose_name='Краткое наименование', default=default_map)
    full_name = models.JSONField(
        verbose_name='Краткое наименование', null=True, blank=True, default=default_map)
    code = models.CharField(
        max_length=128, verbose_name='Код', unique=False, null=True, blank=True)
    abc_dictionary = models.ForeignKey(
        to=ABCDictionary, on_delete=models.SET_NULL, null=True, verbose_name='Справочник')
    parent = models.ForeignKey(
        "self", null=True, blank=True, related_name="children",
        on_delete=models.CASCADE, verbose_name='Родительский элемент')
    active = models.BooleanField(
        default=True, verbose_name='Активный')
    author = models.ForeignKey(
        to="User", on_delete=models.SET_NULL, null=True, verbose_name='Автор', related_name="element")
    organization = models.ForeignKey(
        to="organization", on_delete=models.SET_NULL, blank=True, null=True,
        verbose_name='Организация', related_name="element")

    def __str__(self):
        return self.short_name.get("ru", "No name")

    class Meta:
        db_table = '"dct\".\"element"'
        verbose_name = 'DCT Элемент'
        verbose_name_plural = 'DCT Элементы'


class ElementIndicatorValue(IndicatorValueBase):
    """
    Значения индикаторов по Элементам
    """
    element = models.ForeignKey(
        to=Element, on_delete=models.CASCADE, verbose_name='Элемент',
        related_name="element_value")
    indicator = models.ForeignKey(
        to=DctIndicator, on_delete=models.CASCADE, verbose_name='Показатель',
        related_name="indicator_value")
    author = models.ForeignKey(
        to="User", on_delete=models.SET_NULL, null=True, verbose_name='Автор')

    class Meta:
        db_table = '"dct\".\"indicator_value"'
        verbose_name = 'DCT Значение инициатора'
        verbose_name_plural = 'DCT Значение индикаторов'

    def __str__(self):
        return self.value_str or str(self.value_int) or self.value_text or str(self.value_datetime)

    def save(self, *args, **kwargs):
        """Автоматическое заполнение сортировки"""
        if not self.pk:
            max_sort = ElementIndicatorValue.objects.aggregate(models.Max('index_sort'))['index_sort__max']
            if max_sort is None:
                max_sort = 0
            self.index_sort = max_sort + 5
        super().save(*args, **kwargs)

    @staticmethod
    def json_file_data(filename, file_id):
        file_data = {"filename": filename, "file_id": file_id}
        return json.dumps(file_data)


class ElementHistory(models.Model):
    """
    Истрория действии над :Elements
    """
    stamp = models.JSONField(verbose_name='Слепок', null=True, blank=True)
    action = models.CharField(max_length=128, null=True, blank=True, verbose_name='Действие')
    element = models.ForeignKey(
        to=Element, on_delete=models.SET_NULL, null=True, verbose_name='Элемент',
        related_name="element_history")
    author = models.ForeignKey(
        to="User", on_delete=models.SET_NULL, null=True, verbose_name='Автор')
    created_at = models.DateTimeField(
        auto_now_add=True, blank=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(
        auto_now=True, blank=True, verbose_name='Дата обновления')

    def __str__(self):
        return self.action

    class Meta:
        db_table = '"dct\".\"element_history"'
        verbose_name = 'DCT История элемента'
        verbose_name_plural = 'DCT История элементов'


# Models for Documents schemas
class ABCDocument(models.Model):
    """
    Абстракция документа
    """
    name = models.JSONField(
        verbose_name='Наименование', default=default_map)
    description = models.JSONField(
        null=True, blank=True, verbose_name='Описание', default=default_map)
    code = models.CharField(
        max_length=128, verbose_name='Код', unique=True)
    author = models.ForeignKey(
        to="User", on_delete=models.CASCADE, verbose_name='Автор')
    parent = models.ForeignKey(
        "self", null=True, blank=True, related_name="children",
        on_delete=models.CASCADE, verbose_name='Родительский элемент')

    def __str__(self):
        return self.name.get("ru", "No name")

    class Meta:
        db_table = '"dcm\".\"abc_document"'
        verbose_name = 'DCM Документ'
        verbose_name_plural = 'DCM Документы'


class IndicatorParameter(ParameterBase):
    """
    Параметры по умолчанию
    """
    class Meta:
        db_table = '"dcm\".\"idc_parameter"'
        verbose_name = 'Параметр'
        verbose_name_plural = 'Параметры'


class DcmIndicator(IndicatorBase):
    """
    Показатели :ABCDocument
    """
    custom_rule = models.JSONField(verbose_name='Правило', null=True, blank=True)
    abc_document = models.ForeignKey(
        to=ABCDocument, on_delete=models.CASCADE, verbose_name='Документ',
        related_name='indicator')
    reference = models.PositiveIntegerField(
        null=True, blank=True, verbose_name='Внешний ключ')
    parameters = models.ManyToManyField(
        IndicatorParameter, blank=True, verbose_name='Параметры')
    author = models.ForeignKey(to="User", on_delete=models.SET_NULL, null=True, verbose_name='Автор',
                               related_name="indicator")

    def __str__(self):
        return self.name.get("ru", "No name")

    class Meta:
        db_table = '"dcm\".\"dcm_indicator"'
        verbose_name = 'DCM Индикатор'
        verbose_name_plural = 'DCM Индикаторы'

    def save(self, *args, **kwargs):
        """
        Счетчик сортировки +5
        """
        if not self.pk:
            max_sort = DcmIndicator.objects.aggregate(models.Max('index_sort'))['index_sort__max']
            if max_sort is None:
                max_sort = 0
            self.index_sort = max_sort + 5
        super().save(*args, **kwargs)


class Record(SoftDelete):
    """
    Запсиси :ABCDocument
    """
    number = models.CharField(verbose_name="Номер", max_length=255)
    date = models.DateField(verbose_name="Дата")
    created_at = models.DateTimeField(auto_now_add=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True)
    active = models.BooleanField(default=True, verbose_name="Активный")
    abc_document = models.ForeignKey(
        to=ABCDocument, on_delete=models.SET_NULL, null=True,
        verbose_name='Документ')
    parent = models.ForeignKey(
        "self", null=True, blank=True, related_name="children", on_delete=models.CASCADE,
        verbose_name='Родительский элемент')
    author = models.ForeignKey(
        to="User", on_delete=models.CASCADE, verbose_name='Автор')
    organization = models.ForeignKey(
        to="organization", on_delete=models.SET_NULL, blank=True, null=True,
        verbose_name='Организация', related_name="record")

    def __str__(self):
        return self.number

    class Meta:
        db_table = '"dcm\".\"record"'
        verbose_name = 'DCM Запись документа'
        verbose_name_plural = 'DCM Записи документов'


class RecordIndicatorValue(IndicatorValueBase):
    """
    Значения индикаторов по Записям
    """
    record = models.ForeignKey(
        to=Record, on_delete=models.CASCADE, verbose_name='Запсиь',
        related_name="record_value")
    indicator = models.ForeignKey(
        to=DcmIndicator, on_delete=models.CASCADE, verbose_name='Показатель',
        related_name="indicator_value")

    def __str__(self):
        return self.value_str or self.value_text or str(self.value_datetime) or str(self.value_int)

    class Meta:
        db_table = '"dcm\".\"indicator_value"'
        verbose_name = 'DCM Значение инидкатора'
        verbose_name_plural = 'DCM Значения индикаторов'

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


class RecordHistory(models.Model):
    """
    История действии над :Record
    """
    status = models.CharField(
        max_length=28,
        default="created",
        verbose_name='Статус')
    status_comment = models.TextField(
        max_length=312, null=True, blank=True, verbose_name='Комментарий')
    stage = models.CharField(max_length=128, null=True, blank=True, verbose_name='Этап')
    action = models.CharField(max_length=128, null=True, blank=True, verbose_name='Действие')
    signature = models.BooleanField(null=True, blank=True, verbose_name='Подписание')
    sign_stamp = models.TextField(verbose_name='Ключ верификации', null=True, blank=True)
    stamp = models.JSONField(verbose_name='Слепок', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True)
    author = models.ForeignKey(
        to="User", on_delete=models.CASCADE, verbose_name='Автор')
    record = models.ForeignKey(
        to=Record, on_delete=models.SET_NULL, null=True,
        verbose_name='Журнал документа', related_name="record_history")

    def __str__(self):
        return self.action

    class Meta:
        db_table = '"dcm\".\"record_history"'
        verbose_name = 'DCM История записи'
        verbose_name_plural = 'DCM Истории записей'


# Models for System schemas
class PFEnum(models.Model):
    """
    Словарь перечислении
    """
    list = models.CharField(max_length=128, verbose_name='Код списка')
    code = models.CharField(max_length=128, verbose_name='Код элемента')
    short_name = models.JSONField(
        verbose_name='Краткое наименование', default=default_map)
    full_name = models.JSONField(
        verbose_name='Полное наименование', null=True, blank=True, default=default_map)
    active = models.BooleanField(default=True, verbose_name='Активный')
    author = models.ForeignKey(
        to="User", on_delete=models.CASCADE, verbose_name='Автор', related_name="enum")

    def __str__(self):
        return self.list

    class Meta:
        db_table = '"sys\".\"pf_enum"'
        verbose_name = 'SYS Перечисление'
        verbose_name_plural = 'SYS Перечисления'


class NotificationType(Enum):
    INFO = 'info'
    WARNING = 'warning'
    REMINDER = 'reminder'
    ERROR = 'error'

    @classmethod
    def choices(cls):
        return [(tag.value, tag.name) for tag in cls]


class Notification(models.Model):
    """
    Уведомления
    """
    title = models.CharField(max_length=128, verbose_name='Заголовок')
    message = models.TextField(verbose_name='Сообщение')
    is_read = models.BooleanField(default=False, verbose_name='Прочитано')
    read_at = models.DateTimeField(auto_now=True, blank=True, null=True)
    type_notification = models.CharField(
        max_length=20,
        choices=NotificationType.choices(),
        default=NotificationType.INFO.value,
        verbose_name='Тип уведомления'
    )
    created_at = models.DateTimeField(auto_now_add=True, blank=True)
    user = models.ForeignKey(
        to="User", on_delete=models.CASCADE, verbose_name='Получатель')
    source_user = models.ForeignKey(
        to="User", on_delete=models.CASCADE, verbose_name='Отправитель', related_name='notification_source')
    record = models.ForeignKey(
        to=Record, on_delete=models.CASCADE, verbose_name='Запись', null=True, blank=True)

    class Meta:
        db_table = '"sys\".\"notification"'
        verbose_name = 'SYS Уведомление'
        verbose_name_plural = 'SYS Уведомления'


class Organization(models.Model):
    """
    Организации
    """
    name = models.JSONField(verbose_name='Наименование организации', default=default_map)
    identifier = models.CharField(max_length=128, null=True, blank=True, verbose_name='БИН')
    address = models.CharField(max_length=128, null=True, blank=True, verbose_name='Адрес')
    created_at = models.DateTimeField(auto_now_add=True, blank=True)

    def __str__(self):
        return self.name.get("ru", "No name")

    class Meta:
        db_table = '"sys\".\"organization"'
        verbose_name = "SYS Организация"
        verbose_name_plural = "SYS Организации"


# Model custom User
class User(AbstractUser):
    """
    Пользователь
    """
    avatar = models.ImageField(upload_to='users', verbose_name='Фото профиля', null=True, blank=True)
    is_blocked = models.BooleanField(default=False, verbose_name='Заблокирован')
    organization = models.ForeignKey(
        to=Organization, on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name='Организация', related_name='user_organization')

    def __str__(self):
        return self.username

    class Meta:
        db_table = '"sys\".\"user"'
        verbose_name = 'SYS Пользователь'
        verbose_name_plural = 'SYS Пользователи'
