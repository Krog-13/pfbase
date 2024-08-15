import os
from django.db import models
from django.utils.text import slugify
from IEF.base_model import CategoryBase, IndicatorBase, DefaultParameterBase, IndicatorValueBase, SoftDelete
from users.models import Organization, User


class CategoryReport(CategoryBase):
    """
    Категории отчетов
    """

    class Meta:
        db_table = '"rpt\".\"category_report"'
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
    naming = models.JSONField(
        max_length=255, verbose_name='Наименование', null=True, blank=True)
    description = models.TextField(
        null=True, blank=True, verbose_name='Описание')
    abc_code = models.CharField(max_length=128, verbose_name='Код', null=True, blank=True)
    organizations = models.ManyToManyField(
        to=Organization, blank=True, verbose_name='Организация')
    category_report = models.ForeignKey(
        CategoryReport, null=True, blank=True, on_delete=models.SET_NULL, verbose_name='Категория документа')
    author = models.ForeignKey(
        to=User, on_delete=models.CASCADE, verbose_name='Автор')

    def __str__(self):
        return self.naming["short_name"]

    class Meta:
        db_table = '"rpt\".\"abc_reports"'
        verbose_name = 'Отчёт'
        verbose_name_plural = 'Отчёты'

    def save(self, *args, **kwargs):
        if self.full_name or self.part_name:
            self.naming = {"full_name": self.full_name, "short_name": self.part_name}
        super().save(*args, **kwargs)


class JournalReport(SoftDelete):
    """
    Отчеты
    """
    _PERIODS = [("day", "ежедневный"), ("month", "ежемесячный"), ("quarter", "квартальный"),
                ("year", "годовой")]
    period = models.CharField(
        max_length=128, choices=_PERIODS, verbose_name='Период')
    period_value = models.CharField(verbose_name="Значание периода", null=True, blank=True)
    short_name = models.CharField(
        max_length=128, unique=True, verbose_name='Наименование')
    code = models.CharField(max_length=128, verbose_name='Код', null=True, blank=True)
    rpt_number = models.CharField(max_length=216, verbose_name='Номер отчета', null=True, blank=True)
    date_time = models.DateTimeField(verbose_name="Дата создания", null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True)
    author = models.ForeignKey(
        to=User, on_delete=models.CASCADE, verbose_name='Автор')
    abc_report = models.ForeignKey(to=ABCReport, null=True, blank=True, on_delete=models.SET_NULL,
                                     verbose_name='Отчет')
    parent = models.ForeignKey("self", null=True, blank=True, related_name="children", on_delete=models.SET_NULL,
                               verbose_name='Родительский элемент')

    def __str__(self):
        return self.short_name

    class Meta:
        db_table = '"rpt\".\"journal"'
        verbose_name = 'Журнал Отчета'
        verbose_name_plural = 'Журнал Отчетов'


class HistoryReportJournal(models.Model):
    """History of Report"""
    journal_status = models.CharField(max_length=128, verbose_name='Статус')
    status_comment = models.TextField(max_length=312, null=True, blank=True, verbose_name='Комментарий')
    created_at = models.DateTimeField(auto_now_add=True, blank=True)
    journal_stamp = models.JSONField(verbose_name='Слепок', null=True, blank=True)
    author = models.ForeignKey(
        to=User, on_delete=models.CASCADE, verbose_name='Автор')
    journal_report = models.ForeignKey(to=JournalReport, null=True, blank=True, on_delete=models.SET_NULL,
                                         verbose_name='Журнал отчетов', related_name="history_status")

    class Meta:
        db_table = '"rpt\".\"history_report_journal"'
        verbose_name = 'История Журнала'
        verbose_name_plural = 'Истории Журнала'


class DefaultParameter(DefaultParameterBase):
    """
    Параметры для показателя
    """
    class Meta:
        db_table = '"rpt\".\"default_parameter"'
        verbose_name = 'Параметр'
        verbose_name_plural = 'Параметры'


class ReportIndicator(IndicatorBase):
    """
    Показатели
    """
    idc_code = models.CharField(max_length=128, verbose_name='Код', null=True, blank=True)
    custom_rule = models.JSONField(max_length=255, verbose_name='Правило', null=True, blank=True)
    report = models.ForeignKey(
        to=ABCReport, on_delete=models.CASCADE, verbose_name='Отчет', null=True,
        related_name='report_indicators')
    reference = models.PositiveIntegerField(null=True, blank=True, verbose_name="Foreign Key")
    parameters = models.ManyToManyField(
        DefaultParameter, blank=True, verbose_name='Параметры')

    class Meta:
        db_table = '"rpt\".\"indicator"'
        verbose_name = 'Показатель'
        verbose_name_plural = 'Показатели'


class IndicatorValue(IndicatorValueBase):
    """
    Значения показателей
    """
    journal_report = models.ForeignKey(
        to=JournalReport, on_delete=models.CASCADE, verbose_name='Журнал отчета',
        related_name="journal_rpt")
    indicator = models.ForeignKey(
        to=ReportIndicator, on_delete=models.CASCADE, verbose_name='Показатель',
        related_name="indicator_rpt")

    class Meta:
        db_table = '"rpt\".\"indicator_values"'
        verbose_name = 'Значение показателя'
        verbose_name_plural = 'Значения показателей'

    def __str__(self):
        return self.indicator_value if self.indicator_value else self.indicator.short_name
