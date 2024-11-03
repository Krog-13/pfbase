from django.db.models import Max, F
from django.db import models
from ..base_models import IndicatorType
from django.utils import timezone
from datetime import datetime
# from django.db.models.functions import TruncDate


class RecordsManager(models.Manager):
    def getByFilter(self, params):
        output = self.findByQuery(params)
        return output

    def findByQuery(self, params):
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
                    history__status_id=value,
                    history__created_at=F('latest_status_date')
                )
        return quryset

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
