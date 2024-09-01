import os
from django.db import models
from django.utils.text import slugify
from IEF.base_model import CategoryBase, IndicatorBase, ParameterBase, IndicatorValueBase, SoftDelete
from users.models import Organization, User


class Category(CategoryBase):
    """
    Категории отчетов
    """
    class Meta:
        db_table = '"rpt\".\"category"'
        verbose_name = 'Категорию отчета'
        verbose_name_plural = 'Категории отчетов'


def generate_filename(instance, filename=None, is_link=False):
    """
    Генерация имени файла
    """
    if filename:
        if is_link:
            filename.replace("templates/", "")
        filename_without_extension = os.path.splitext(filename)[0]
        slugified_filename = slugify(
            filename_without_extension, allow_unicode=True)
        extension = os.path.splitext(filename)[-1]
        if is_link:
            return f"{slugified_filename}{extension}"
        else:
            return f"templates/{slugified_filename}{extension}"

    return None


def generate_filename_instruction(instance, filename=None, is_link=False):
    """
    Генерация имени файла инструкции
    """
    if filename:
        if is_link:
            filename.replace("templates/instructions/", "")
        filename_without_extension = os.path.splitext(filename)[0]
        slugified_filename = slugify(
            filename_without_extension, allow_unicode=True)
        extension = os.path.splitext(filename)[-1]
        if is_link:
            return f"{slugified_filename}{extension}"
        else:
            return f"templates/instructions/{slugified_filename}{extension}"

    return None


class ABCReport(models.Model):
    """Abstract Report"""
    rpt_name = models.JSONField(verbose_name='Наименование')
    description = models.TextField(
        null=True, blank=True, verbose_name='Описание')
    code = models.CharField(max_length=128, verbose_name='Код', unique=True)
    organizations = models.ManyToManyField(
        to=Organization, blank=True, verbose_name='Организация')
    author = models.ForeignKey(
        to=User, on_delete=models.CASCADE, verbose_name='Автор')

    def __str__(self):
        return self.rpt_name.get("ru", self.code)

    class Meta:
        db_table = '"rpt\".\"abc_report"'
        verbose_name = 'Отчёт'
        verbose_name_plural = 'Отчёты'

    def save(self, *args, **kwargs):
        if self.full_name or self.part_name:
            self.naming = {"full_name": self.full_name, "short_name": self.part_name}
        super().save(*args, **kwargs)


class IndicatorParameter(ParameterBase):
    """
    Default parameters for indicators
    """
    class Meta:
        db_table = '"rpt\".\"indicator_parameter"'
        verbose_name = 'Параметр'
        verbose_name_plural = 'Параметры'


class Indicator(IndicatorBase):
    """
    Indicator for reports
    """
    custom_rule = models.JSONField(verbose_name='Правило', null=True, blank=True)
    abc_report = models.ForeignKey(
        to=ABCReport, on_delete=models.CASCADE, verbose_name='Отчет',
        related_name='indicator')
    reference = models.PositiveIntegerField(
        null=True, blank=True, verbose_name="Внешний ключ")
    parameters = models.ManyToManyField(
        IndicatorParameter, blank=True, verbose_name='Параметры')

    class Meta:
        db_table = '"rpt\".\"indicator"'
        verbose_name = 'Показатель'
        verbose_name_plural = 'Показатели'


class Report(SoftDelete):
    """
    Report
    """
    _PERIODS = [("day", "ежедневный"), ("month", "ежемесячный"), ("quarter", "квартальный"),
                ("year", "годовой")]
    period = models.CharField(
        max_length=128, choices=_PERIODS, verbose_name='Период')
    period_value = models.CharField(verbose_name="Значание периода", null=True, blank=True)
    short_name = models.JSONField(verbose_name='Краткое наименование')
    full_name = models.JSONField(verbose_name='Полное наименование')
    code = models.CharField(
        max_length=128, verbose_name='Код', unique=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True)
    author = models.ForeignKey(
        to=User, on_delete=models.CASCADE, verbose_name='Автор')
    abc_report = models.ForeignKey(to=ABCReport, null=True, blank=True, on_delete=models.SET_NULL,
                                     verbose_name='Отчет')
    parent = models.ForeignKey(
        "self", null=True, blank=True, related_name="children", on_delete=models.CASCADE,
        verbose_name='Родительский элемент')

    def __str__(self):
        return self.short_name.get("ru", self.code)

    class Meta:
        db_table = '"rpt\".\"report"'
        verbose_name = 'Отчета'
        verbose_name_plural = 'Отчеты'


class ReportIndicatorValue(IndicatorValueBase):
    """
    Record-Indicator Value
    """
    value_text = models.TextField(
        null=True, blank=True, verbose_name='Текст')
    value_datetime = models.DateTimeField(
        null=True, blank=True, verbose_name='Дата и время')
    value_reference = models.PositiveIntegerField(
        null=True, blank=True, verbose_name='Внешний ключ')
    record_report = models.ForeignKey(
        to=Report, on_delete=models.CASCADE, verbose_name='Запись отчета',
        related_name="report_value")
    indicator = models.ForeignKey(
        to=Indicator, on_delete=models.CASCADE, verbose_name='Показатель',
        related_name="indicator_value")

    class Meta:
        db_table = '"rpt\".\"indicator_value"'
        verbose_name = 'Значение показателя'
        verbose_name_plural = 'Значения показателей'

    def __str__(self):
        return self.record_report


class ReportJournal(models.Model):
    """History of Report"""
    status = models.CharField(
        max_length=128, verbose_name='Статус')
    status_comment = models.TextField(
        max_length=312, null=True, blank=True, verbose_name='Комментарий')
    created_at = models.DateTimeField(auto_now_add=True, blank=True)
    sign_stamp = models.TextField(verbose_name='Ключ верификации', null=True, blank=True)
    stamp = models.JSONField(verbose_name='Слепок', null=True, blank=True)
    author = models.ForeignKey(
        to=User, on_delete=models.CASCADE, verbose_name='Автор')
    report = models.ForeignKey(
        to=Report, null=True, blank=True, on_delete=models.SET_NULL,
        verbose_name='Журнал отчетов', related_name="history_status")

    class Meta:
        db_table = '"rpt\".\"report_journal"'
        verbose_name = 'История Журнала'
        verbose_name_plural = 'Истории Журнала'
