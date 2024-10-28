from django.db import transaction
from collections import namedtuple
from pfbase.exception import WrongType
from django.utils import timezone
from datetime import datetime
from ..system import models as stm_models
from .models import Elements, DctIndicators, Dictionaries

Typing = namedtuple('Typing', ['int', 'float', 'str', 'text', 'datetime', 'bool', 'reference', 'json'])
marker = Typing(int="int", float="float", str="str", text="text", json='json', datetime=["datetime", "date", "time"],
                bool="bool", reference=["dct", "list"])


class ElementService:

    @transaction.atomic
    def create_element_iv(self, user, validated_data):
        dictionary_id = validated_data.get('dictionary_id')
        code = validated_data.get('code')
        indicators = validated_data.get('indicators')
        parent_id = validated_data.get('parent_id')
        if dictionary_id:
            dictionary = Dictionaries.objects.get(id=dictionary_id)
        else:
            dictionary = Dictionaries.objects.get(code=code)
        parent_e = Elements.objects.get(id=parent_id) if parent_id else None

        element = Elements.objects.create(
            short_name=validated_data.get('short_name'),
            full_name=validated_data.get('full_name'),
            code=validated_data.get('code'),
            dictionary=dictionary,
            author=user,
            parent=parent_e)

        if not indicators:
            return element

        for indicator in indicators:
            some_value = indicator.get('value')
            type_value = indicator.get('type')
            idc_id = indicator.get('id')
            idc_code = indicator.get('code')
            if type_value == marker.reference[1]:
                if not some_value.isdigit():
                    raise WrongType("Invalid type value")
                stm_models.ListValues.objects.get(id=some_value)
            elif type_value == marker.reference[0]:
                if not some_value.isdigit():
                    raise WrongType("Invalid type value")
                Elements.objects.get(id=some_value)
            if idc_id:
                dct_indicator = DctIndicators.objects.get(id=indicator.get('id'), type_value=type_value)
            else:
                dct_indicator = DctIndicators.objects.get(code=idc_code, type_value=type_value)
            ev = element.element_values.create(indicator=dct_indicator)
            result = self.separate_value(ev, type_value, some_value)
            if not result:
                raise WrongType("Invalid type value")
            ev.save()
        return element

    @transaction.atomic
    def update_element_iv(self, element, user, validated_data):
        """
        Update Element with their Indicators
        """
        indicators = validated_data.get('indicators')
        parent_id = validated_data.get('parent_id')
        short_name = validated_data.get('short_name')
        full_name = validated_data.get('full_name')
        code = validated_data.get('code')

        if parent_id:
            parent_element = Elements.objects.get(id=parent_id)
            element.parent = parent_element
        if short_name:
            element.short_name = short_name
        if full_name:
            element.full_name = full_name
        if code:
            element.code = code
        element.user = user
        element.save()

        if not indicators:
            return element

        for indicator in indicators:
            type_value = indicator.get('type')
            rv = element.record_value.get(id=indicator.get('id'), indicator__type_value=type_value)
            some_value = indicator.get('value')
            result = self.separate_value(rv, type_value, some_value)
            if not result:
                raise WrongType("Invalid type value")
            rv.save()
        return element

    def separate_value(self, entity, type_value, some_value):
        if type_value == marker.int:
            entity.value_int = some_value
        elif type_value == marker.float:
            entity.value_float = some_value
        elif type_value == marker.str:
            entity.value_str = some_value
        elif type_value == marker.text:
            entity.value_text = some_value
        elif type_value == marker.bool:
            entity.value_bool = some_value
        elif type_value in marker.reference:
            entity.value_reference = some_value
        elif type_value == marker.json:
            entity.value_json = some_value
        elif type_value in marker.datetime:
            date = self.give_date_format(some_value, type_value)
            if not date:
                return False
            entity.value_datetime = date
        else:
            return False
        return True

    @staticmethod
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


def find_driver(queryset, params):
    output = {"drivers": []}
    indicators = params.get('indicators')
    drivers = queryset.filter(element_values__value_str__contains=params.get('search'))
    for driver in drivers:
        driver_iv = driver.element_values.all()
        values = {"data": [], "id": None}
        for idc in indicators.split(","):
            value = driver_iv.filter(indicator__code=idc).first()
            if value:
                values["data"].append(value.value_str)
        values["id"] = driver.id
        output["drivers"].append(values)
    return output
