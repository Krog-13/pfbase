from django.db import transaction
from collections import namedtuple
from pfbase.exception import WrongType
from django.utils import timezone
from datetime import datetime
from ..system import models as stm_models
from ..dictionary import models as dct_models
from .models import Records, DcmIndicators, Documents

Typing = namedtuple('Typing', ['int', 'str', 'text', 'datetime', 'bool', 'reference', 'json'])
marker = Typing(int="int", str="str", text="text", json='json', datetime=["datetime", "date", "time"],
                bool="bool", reference=["dct", "enum"])


class RecordService:

    @transaction.atomic
    def create_record_iv(self, user, validated_data):
        """
        Create Record with their Indicators
        """
        document_id = validated_data.get('document_id')
        indicators = validated_data.get('indicators')
        parent_id = validated_data.get('parent_id')
        document = Documents.objects.get(id=document_id)

        parent_r = Records.objects.get(id=parent_id) if parent_id else None
        record = Records.objects.create(
            number=validated_data.get('number'),
            date=validated_data.get('date'),
            parent=parent_r,
            author=user,
            abc_document=document)

        if not indicators:
            return record
        for indicator in indicators:
            some_value = indicator.get('value')
            type_value = indicator.get('type')
            if type_value == marker.reference[1]:
                if not some_value.isdigit():
                    raise WrongType("Invalid type value")
                stm_models.ListValues.objects.get(id=some_value)
            elif type_value == marker.reference[0]:
                if not some_value.isdigit():
                    raise WrongType("Invalid type value")
                dct_models.Elements.objects.get(id=some_value)

            dcm_indicator = DcmIndicators.objects.get(id=indicator.get('id'), type_value=type_value)
            rv = record.record_value.create(indicator=dcm_indicator)
            result = self.separate_value(rv, type_value, some_value)
            if not result:
                raise WrongType("Invalid type value")
            rv.save()
        return record

    @transaction.atomic
    def update_record_iv(self, record, user, validated_data):
        """
        Update Record with their Indicators
        """
        indicators = validated_data.get('indicators')
        parent_id = validated_data.get('parent_id')
        number = validated_data.get('number')
        date = validated_data.get('date')
        if parent_id:
            parent_record = Records.objects.get(id=parent_id)
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
            rv = record.record_value.get(id=indicator.get('id'), indicator__type_value=type_value)
            some_value = indicator.get('value')
            result = self.separate_value(rv, type_value, some_value)
            if not result:
                raise WrongType("Invalid type value")
            rv.save()
        return record

    def separate_value(self, entity, type_value, some_value):
        if type_value == marker.int:
            entity.value_int = some_value
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
