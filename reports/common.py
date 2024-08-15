from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from .models import JournalReport, HistoryReportJournal, ReportIndicator, IndicatorValue
from documents.models import FieldValue
from reports.serializers import JournalDetailSerializer
from django.db import IntegrityError, transaction
import logging.config
import random
from django.db.models import Sum, Max, Min, Avg, IntegerField
from django.db.models.functions import Cast
from datetime import datetime, timedelta
import calendar

# init logging
logger = logging.getLogger("ief_logger")


def journal_history_create(journal, author, stamp):
    if stamp:
        try:
            obj = JournalReport.everything.get(id=journal.get("journal_document_id"))
        except JournalReport.DoesNotExist:
            return Response({"Msg": "Journal document does not exist"},
                     status=status.HTTP_400_BAD_REQUEST)
        serializer = JournalDetailSerializer(obj)
        data_stamp = serializer.data
    else:
        data_stamp = None
    HistoryReportJournal.objects.create(
        journal_status=journal.get("journal_status"),
        status_comment=journal.get("status_comment"),
        journal_document_id=journal.get("journal_report_id"),
        author=author,
        data_stamp=data_stamp)
    return Response({"Msg": "Journal History Created"},
                    status=status.HTTP_201_CREATED)


def sum_indicator(date_start, date_end, rule):
    """Calculate sum indicators by code"""
    codes = rule["doc"]["sum"]["idc_code"]
    result = FieldValue.objects.filter(indicator__idc_code__in=codes, journal_document__date_time__range=(date_start, date_end)).aggregate(total=Sum(Cast("indicator_value", IntegerField())))
    return result

def max_indicator(date_start, date_end, rule):
    codes = rule["doc"]["max"]["idc_code"]
    result = FieldValue.objects.filter(indicator__idc_code__in=codes,
                                       journal_document__date_time__range=(date_start, date_end)).aggregate(
        total=Max(Cast("indicator_value", IntegerField())))
    return result

def min_indicator(date_start, date_end, rule):
    codes = rule["doc"]["min"]["idc_code"]
    result = FieldValue.objects.filter(indicator__idc_code__in=codes,
                                       journal_document__date_time__range=(date_start, date_end)).aggregate(
        total=Min(Cast("indicator_value", IntegerField())))
    return result

def avg_indicator(date_start, date_end, rule):
    codes = rule["doc"]["avg"]["idc_code"]
    result = FieldValue.objects.filter(indicator__idc_code__in=codes,
                                       journal_document__date_time__range=(date_start, date_end)).aggregate(
        total=Avg(Cast("indicator_value", IntegerField())))
    return result

def get_quarter_dates(period_value):
    item = period_value.split(',')
    year = int(item[0])
    quarter = int(item[1])
    if quarter not in [1, 2, 3, 4]:
        raise ValueError("Quarter must be between 1 and 4")

    month_ranges = [(1, 3), (4, 6), (7, 9), (10, 12)]
    start_month, end_month = month_ranges[quarter - 1]

    _, days_in_start_month = calendar.monthrange(year, start_month)
    _, days_in_end_month = calendar.monthrange(year, end_month)

    start_date = timezone.make_aware(datetime(year, start_month, 1))
    end_date = timezone.make_aware(datetime(year, end_month, days_in_end_month))
    return start_date, end_date

def get_period(journal):
    period_value = journal["period_value"]
    period = journal["period"]
    if period.lower() == "ежемесячный":
        period_start = timezone.make_aware(datetime.strptime(period_value, "%Y-%m-%d"))
        _, last_day = calendar.monthrange(period_start.year, period_start.month)
        period_end = timezone.make_aware(datetime(period_start.year, period_start.month, last_day))
    elif period.lower() == "квартальный":
        period_start, period_end = get_quarter_dates(period_value)
    elif period.lower() == "годовой":
        period_start = timezone.make_aware(datetime.strptime(period_value, "%Y-%m-%d"))
        _, last_day = calendar.monthrange(period_start.year, period_start.month)
        period_end = timezone.make_aware(datetime(period_start.year, period_start.month, last_day))
    else:
        period_start, period_end = None, None
    return period_start, period_end

@transaction.atomic
def journal_create(journal, indicators, user):
    random_number = random.randint(100000, 999999)
    random_name = random.randint(1, 999)
    report_id = journal["report_id"]

    report_indicators = ReportIndicator.objects.filter(report=report_id)
    period_start, period_end = get_period(journal)
    value_rule = None
    for item in report_indicators:
        if rule := item.custom_rule:
            if rule.get("doc"):
                if "sum" in rule["doc"]:
                    value_rule = sum_indicator(period_start, period_end, rule)
                elif "max" in rule["doc"]:
                    value_rule = max_indicator(period_start, period_end, rule)
                elif "min" in rule["doc"]:
                    value_rule = min_indicator(period_start, period_end, rule)
                elif "avg" in rule["doc"]:
                    value_rule = avg_indicator(period_start, period_end, rule)
                else:
                    value_rule = None
            else:
                value_rule = None
    # return Response({}, status=status.HTTP_201_CREATED)
    print(value_rule)
    try:
        elm = JournalReport.objects.create(
            period=journal["period"],
            period_value=journal["period_value"],
            short_name=f"Document-{random_name}",
            rpt_number=random_number,
            date_time=timezone.now(),
            abc_report_id=journal["report_id"],
            parent_id=journal.get("parent_id"),
            author=user)
    except IntegrityError:
        return Response({"Msg": "duplicate key value violates unique constraint short_name"},
                        status=status.HTTP_400_BAD_REQUEST)
    values = []
    for item in indicators:
        if item.get("type") == "calc":
            value = calculate_indicator(indicators, item["indicator_id"])
            if not value:
                transaction.set_rollback(True)
                return Response({"msg": "formula incorrect"}, status=status.HTTP_400_BAD_REQUEST)
            item["value"] = value
        elif item.get("type") == "rule":
            item["value"] = value_rule["total"]
        idc_code = item.get("code")

        try:
            indicator_id = ReportIndicator.objects.get(idc_code=idc_code)
        except ReportIndicator.DoesNotExist:
            return Response({"Error msg": f"Code not found - {idc_code}"}, status=status.HTTP_400_BAD_REQUEST)
        values.append(
            IndicatorValue(
                indicator_value=item.get("value"),
                journal_report_id=elm.id,
                indicator_id=indicator_id.id))
    IndicatorValue.objects.bulk_create(values)
    HistoryReportJournal.objects.create(
        journal_status=journal["doc_status"],
        author=user,
        journal_report_id=elm.id)
    return Response({}, status=status.HTTP_201_CREATED)


def calculate_indicator(indicators, indicator_id):
    """Calculation custom formula"""
    calc_indicator = IndicatorValue.objects.get(id=indicator_id)
    custom_rule = calc_indicator.custom_rule
    formula = custom_rule.get("calc")
    for idc in indicators:
        formula = formula.replace(f"{{{idc['indicator_id']}}}", str(idc["value"]))
    try:
        result = eval(formula)
    except (SyntaxError, NameError):
        logger.error("Syntax error formula incorrect")
        return False
    return round(result, 3)