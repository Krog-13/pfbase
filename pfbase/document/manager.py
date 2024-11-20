from django.db.models import Max, F
from django.db import models
from ..base_models import IndicatorType
from django.utils import timezone
from datetime import datetime
from django.db.models import Subquery, OuterRef
from django.db.models import Q


class RecordsManager(models.Manager):
    def getByFilter(self, params):
        output = self.findByQuery(params)
        return output

    def findByQueryOld(self, params):
        """
        Поиск по параметрам
        """
        quryset = self.all()
        for key, value in params.items():
            if key == "CODE":
                quryset = quryset.filter(document__code=value)
            if key == "number":
                quryset = quryset.filter(number=value)
            if key == "record_date":
                quryset = quryset.filter(date__date=value)
            if key == IndicatorType.STRING:
                quryset = quryset.filter(record_values__value_str__contains=value)
            if key == IndicatorType.INTEGER:
                quryset = quryset.filter(record_values__value_int=value)
            if key == IndicatorType.FLOAT:
                quryset = quryset.filter(record_values__value_float=value)
            if key == IndicatorType.BOOLEAN:
                quryset = quryset.filter(record_values__value_bool=value)
            if key == IndicatorType.DICTIONARY:
                quryset = quryset.filter(record_values__value_reference=value)
            if key == IndicatorType.DOCUMENT:
                quryset = quryset.filter(record_values__value_reference=value)
            if key == IndicatorType.LIST:
                quryset = quryset.filter(record_values__value_reference=value)
            if key == IndicatorType.DATETIME:
                # ToDo: сравниваем только date and time без микросекунд
                give_date_format(value, IndicatorType.DATETIME)
                quryset = quryset.filter(record_values__value_datetime=value)
            if key == IndicatorType.DATE:
                quryset = quryset.filter(record_values__value_datetime__date=value)
            if key == IndicatorType.TIME:
                # ToDo: сравниваем только время без микросекунд
                quryset = quryset.filter(record_values__value_datetime__time=value)
            if key == IndicatorType.TEXT:
                quryset = quryset.filter(record_values__value_text=value)
            if key == IndicatorType.JSON:
                quryset = quryset.filter(record_values__value_json=value)

            if key == "STATUS":
                quryset = quryset.annotate(
                    latest_status_date=Max('history__created_at')
                ).filter(
                    history__status_id__in=value,
                    history__created_at=F('latest_status_date')
                )
        return quryset

    def findByQuery(self, params):
        queryset = self.all()
        for key, value in params.items():
            if key == "author_id":
                queryset = queryset.filter(author_id=value)
            if key == "NUMBER":
                queryset = queryset.filter(number=value)
            if key == "DCM_CODE":
                queryset = queryset.filter(document__code=value)
            if key == "active":
                queryset = queryset.filter(active=value)
            if key == "organization_id":
                queryset = queryset.filter(organization=value)
            if key == "parent_id":
                queryset = queryset.filter(parent_id=value)
            if key == "record_date":
                queryset = queryset.filter(date__date=value)
            if key == "STATUS":
                queryset = queryset.annotate(
                    latest_status_date=Max('history__created_at')
                ).filter(
                    history__status_id__in=value,
                    history__created_at=F('latest_status_date')
                )
            if key == "code_status":
                from .models import RecordHistory
                queryset = queryset.annotate(
                    last_status=Subquery(
                        RecordHistory.objects.filter(
                            record=OuterRef('pk')
                        ).order_by('-created_at').values('status__code')[:1]
                    )
                ).filter(last_status=value)

            if key not in ["NUMBER", "DCM_CODE", "active", "organization_id", "parent_id", "page", "lang",
                           "status", "date", "STATUS", "code_status", "record_date", "author_id"]:
                from .models import DcmIndicators
                indic = DcmIndicators.objects.get(code=key)
                if indic.type_value == IndicatorType.STRING:
                    queryset = queryset.filter(record_values__indicator__code=key, record_values__value_str=value)
                elif indic.type_value == IndicatorType.INTEGER:
                    queryset = queryset.filter(record_values__indicator__code=key, record_values__value_int=value)
                elif indic.type_value == IndicatorType.FLOAT:
                    queryset = queryset.filter(record_values__indicator__code=key, record_values__value_float=value)
                elif indic.type_value == IndicatorType.BOOLEAN:
                    queryset = queryset.filter(record_values__indicator__code=key, record_values__value_bool=value)
                elif indic.type_value == IndicatorType.DICTIONARY:
                    queryset = queryset.filter(record_values__indicator__code=key, record_values__value_reference=value)
                elif indic.type_value == IndicatorType.LIST:
                    queryset = queryset.filter(record_values__indicator__code=key, record_values__value_reference=value)
                elif indic.type_value == IndicatorType.DOCUMENT:
                    queryset = queryset.filter(record_values__indicator__code=key, record_values__value_reference=value)
                elif indic.type_value == IndicatorType.TIME:
                    parsed_value = give_date_format(value, "time")
                    if parsed_value:
                        queryset = queryset.filter(
                            record_values__indicator__code=key,
                            record_values__value_datetime__hour=parsed_value.hour,
                            record_values__value_datetime__minute=parsed_value.minute
                        )
                elif indic.type_value == IndicatorType.DATE:
                    parsed_value = give_date_format(value, "date")
                    if parsed_value:
                        queryset = queryset.filter(
                            record_values__indicator__code=key,
                            record_values__value_datetime__date=parsed_value.date()
                        )
                elif indic.type_value == IndicatorType.DATETIME:
                    datetime_only = datetime.strptime(value, "%Y-%m-%d %H:%M")
                    date_only = datetime_only.date()
                    hour_only = datetime_only.hour
                    minute_only = datetime_only.minute
                    queryset = queryset.filter(
                        record_values__indicator__code=key,
                        record_values__value_datetime__date=date_only,
                        record_values__value_datetime__hour=hour_only,
                        record_values__value_datetime__minute=minute_only
                    )
        return queryset


def give_date_format(date_str, type_value):
    """
    Convert str: datetime, date, time to datetime object
    """
    formats = [
        ("%Y-%m-%d %H:%M", "datetime"),  # "2024-01-01 12:33"
        ("%Y-%m-%d", "date"),  # "2024-01-01"
        ("%H:%M", "time")  # "10:23"
    ]
    try:
        for fmt in formats:
            if type_value == fmt[1]:
                parse_datetime = datetime.strptime(date_str, fmt[0])
                if type_value == "time":
                    parse_datetime = datetime.combine(datetime.now().date(), parse_datetime.time())
                return timezone.make_aware(parse_datetime)
    except ValueError:
        return False
