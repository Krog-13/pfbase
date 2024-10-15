"""
Module for tools that are used in the project.
"""

from pfbase.models import Record, ABCDocument, DcmIndicator, Element, ABCDictionary, DctIndicator
from django.db import transaction
from collections import namedtuple
from django.utils import timezone
from .exception import WrongType
from datetime import datetime

Typing = namedtuple('Typing', ['int', 'str', 'text', 'datetime', 'bool', 'reference'])
marker = Typing(int="int", str="str", text="text", datetime=["datetime", "date", "time"],
                bool="bool", reference="dct")


@transaction.atomic
def create_record_row(user, validated_data):
    """
    Create Record with their Indicators
    """
    metadata = validated_data.get('metadata')
    code = metadata.get('document')
    indicators = metadata.get('indicators')
    parent_id = metadata.get('parent_id')
    document = ABCDocument.objects.get(code=code)

    parent_r = Record.objects.get(id=parent_id) if parent_id else None
    if not parent_r:
        raise Record.DoesNotExist
    record = Record.objects.create(
        number=metadata.get('number'),
        date=metadata.get('date'),
        parent=parent_r,
        author=user,
        abc_document=document
    )
    if not indicators:
        return record
    for indicator in indicators:
        type_value = indicator.get('type')
        dcm_indicator = DcmIndicator.objects.get(code=indicator.get('code'))
        rv = record.record_value.create(indicator=dcm_indicator)
        some_value = indicator.get('value')
        result = separate_value(rv, type_value, some_value)
        if not result:
            raise WrongType("Invalid type value")
        rv.save()
    return record


@transaction.atomic
def update_record_row(user, validated_data, record):
    """
    Update Record with their Indicators
    """
    metadata = validated_data.get('metadata')
    indicators = metadata.get('indicators')
    parent_id = metadata.get('parent_id')
    number = metadata.get('number')
    date = metadata.get('date')
    if parent_id:
        parent_record = Record.objects.get(id=parent_id)
        record.parent = parent_record
    if number:
        record.number = number
    if date:
        record.date = date
    record.user = user
    record.save()

    if not indicators:
        return record

    for indicator in indicators:
        type_value = indicator.get('type')
        rv = record.record_value.get(id=indicator.get('id'))
        some_value = indicator.get('value')
        result = separate_value(rv, type_value, some_value)
        if not result:
            raise WrongType("Invalid type value")
        rv.save()
    return record


def give_date_format(date_str, type_value):
    """
    Convert str: datetime, date, time to datetime object
    """
    formats = [
        ("%Y-%m-%d %H:%M", "datetime"),  # "2024-01-01 12:33"
        ("%Y-%m-%d", "date"),            # "2024-01-01"
        ("%H:%M", "time")                # "10:23"
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


@transaction.atomic
def create_element_row(user, validated_data):
    """
    Create Element with their Indicators
    """
    metadata = validated_data.get('metadata')
    abc_code = metadata.get('dictionary')
    indicators = metadata.get('indicators')
    parent_id = metadata.get('parent_id')

    dictionary = ABCDictionary.objects.get(code=abc_code)
    parent_e = Element.objects.get(id=parent_id) if parent_id else None
    if not parent_e:
        raise Element.DoesNotExist

    element = Element.objects.create(
        short_name=metadata.get('short_name'),
        full_name=metadata.get('full_name'),
        code=metadata.get('code'),
        abc_dictionary=dictionary,
        author=user,
        parent=parent_e)

    if not indicators:
        return element

    for indicator in indicators:
        type_value = indicator.get('type')
        dcm_indicator = DctIndicator.objects.get(code=indicator.get('code'))
        ev = element.element_value.create(indicator=dcm_indicator)
        some_value = indicator.get('value')

        result = separate_value(ev, type_value, some_value)
        if not result:
            raise WrongType("Invalid type value")
        ev.save()
    return element


@transaction.atomic
def update_element_row(user, validated_data, element):
    """
    Update Element with their Indicators
    """
    metadata = validated_data.get('metadata')
    indicators = metadata.get('indicators')
    parent_id = metadata.get('parent_id')
    short_name = metadata.get('short_name')
    full_name = metadata.get('full_name')
    code = metadata.get('code')

    if parent_id:
        parent_element = Element.objects.get(id=parent_id)
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
        ev = element.element_value.get(id=indicator.get('id'))
        some_value = indicator.get('value')

        result = separate_value(ev, type_value, some_value)
        if not result:
            raise WrongType("Invalid type value")
        ev.save()
    return element


def separate_value(entity, type_value, some_value):
    if type_value == marker.int:
        entity.value_int = some_value
    elif type_value == marker.str:
        entity.value_str = some_value
    elif type_value == marker.text:
        entity.value_text = some_value
    elif type_value == marker.bool:
        entity.value_bool = some_value
    elif type_value == marker.reference:
        entity.value_reference = some_value
    elif type_value in marker.datetime:
        date = give_date_format(some_value, type_value)
        if not date:
            return False
        entity.value_datetime = date
    else:
        return False
    return True
