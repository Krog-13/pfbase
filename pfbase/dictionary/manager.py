from django.db import models
from django.utils import timezone
from django.db.models import Q
from datetime import datetime
from ..base_models import IndicatorType


class ElementManager(models.Manager):
    def getByCode(self, code):
        return self.get(code=code).id

    def getById(self, id):
        return self.get(id=id).code
    
    def getByFilter(self, params):
        output = self.findByQuery(params)
        return output
    
    def findByQuery(self, params):
        queryset = self.all()
        for key, value in params.items():
            if key == "short_name":
                queryset = queryset.filter(
                    Q(short_name__ru__icontains=value) |
                    Q(short_name__en__icontains=value) |
                    Q(short_name__kk__icontains=value)
                )
            if key == "full_name":
                queryset = queryset.filter(
                    Q(full_name__ru__icontains=value) |
                    Q(full_name__en__icontains=value) |
                    Q(full_name__kk__icontains=value)
                )
            if key == "DICT_CODE":
                queryset = queryset.filter(dictionary__code=value)
            if key == "CODE":
                queryset = queryset.filter(code=value)
            if key == "active":
                queryset = queryset.filter(active=value)
            if key == "organization_id":
                queryset = queryset.filter(organization__in=value)
            if key == "parent_id":
                queryset = queryset.filter(parent=value)
            if key not in ["short_name", "paginate", "full_name", "DICT_CODE", "CODE", "active", "organization_id", "parent_id", "page"]:
                from .models import DctIndicators
                indic = DctIndicators.objects.get(code=key)
                if indic.type_value == IndicatorType.STRING:
                    queryset = queryset.filter(element_values__indicator__code=key,element_values__value_str=value)
                elif indic.type_value == IndicatorType.INTEGER:
                    queryset = queryset.filter(element_values__indicator__code=key,element_values__value_int=value)
                elif indic.type_value == IndicatorType.FLOAT:
                    queryset = queryset.filter(element_values__indicator__code=key,element_values__value_float=value)
                elif indic.type_value == IndicatorType.BOOLEAN:
                    queryset = queryset.filter(element_values__indicator__code=key,element_values__value_bool=value)
                elif indic.type_value == IndicatorType.DICTIONARY:
                    queryset = queryset.filter(element_values__indicator__code=key,element_values__value_reference=value)
                elif indic.type_value == IndicatorType.LIST:
                    queryset = queryset.filter(element_values__indicator__code=key,element_values__value_reference=value)
                elif indic.type_value == IndicatorType.DOCUMENT:
                    queryset = queryset.filter(element_values__indicator__code=key,element_values__value_reference=value)
                elif indic.type_value == IndicatorType.TIME:
                    parsed_value = give_date_format(value, "time")
                    if parsed_value:
                        queryset = queryset.filter(
                            element_values__indicator__code=key,
                            element_values__value_datetime__hour=parsed_value.hour,
                            element_values__value_datetime__minute=parsed_value.minute
                        )
                elif indic.type_value == IndicatorType.DATE:
                    parsed_value = give_date_format(value, "date")
                    if parsed_value:
                        queryset = queryset.filter(
                            element_values__indicator__code=key,
                            element_values__value_datetime__date=parsed_value.date()
                        )
                elif indic.type_value == IndicatorType.DATETIME:
                    datetime_only = datetime.strptime(value, "%Y-%m-%d %H:%M")
                    date_only = datetime_only.date()
                    hour_only = datetime_only.hour
                    minute_only = datetime_only.minute
                    queryset = queryset.filter(
                        element_values__indicator__code=key,
                        element_values__value_datetime__date=date_only,
                        element_values__value_datetime__hour=hour_only,
                        element_values__value_datetime__minute=minute_only
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
    
