from django.db import transaction
from collections import namedtuple
from pfbase.exception import WrongType
from django.utils import timezone
from datetime import datetime
from ..system import models as stm_models
from ..dictionary import models as dct_models
from .models import Records, DcmIndicators, Documents
from django.db.models import Case, When, IntegerField

Typing = namedtuple('Typing', ['int', 'str', 'text', 'datetime', 'bool', 'reference', 'json'])
marker = Typing(int="int", str="str", text="text", json='json', datetime=["datetime", "date", "time"],
                bool="bool", reference=["dct", "list"])


class RecordService:

    @transaction.atomic
    def create_record_iv(self, user, validated_data):
        """
        Create Record with their Indicators
        """
        document_id = validated_data.get('document_id')
        indicators = validated_data.get('indicators')
        parent_id = validated_data.get('parent_id')
        status = validated_data.get('status')
        document = Documents.objects.get(id=document_id)

        parent_r = Records.objects.get(id=parent_id) if parent_id else None
        record = Records.objects.create(
            number=validated_data.get('number'),
            date=validated_data.get('date'),
            parent=parent_r,
            author=user,
            document=document)

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
            rv = record.record_values.create(indicator=dcm_indicator)
            result = self.separate_value(rv, type_value, some_value)
            if not result:
                raise WrongType("Invalid type value")
            rv.save()
        if status:
            self.create_history(record, status, user)
        return record

    def create_history(self, record, status, user):
        status_list_id = status.get("status_list_id")
        comment = status.get("comment")
        status_msg = status.get("status", "created")
        stage = status.get("stage")
        record.history.create(
            status_list_id=status_list_id,
            status=status_msg,
            stage=stage,
            author=user,
            status_comment=comment)

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


class TableService:

    def __init__(self, queryset, params):
        self.queryset = queryset
        self.params = params
        self.output = {"header": [], "body": []}
        self.row = []
        self.status = None

    def construction_table(self):
        self.document_code = self.params.get('document_code')
        self.lang = self.params.get('lang')
        self.status = self.params.get('status', False)
        indicators_code = self.params.get('indicators_code')
        self.order_indicators_code = indicators_code.split(",")
        table_header = self.table_header()
        self.queryset = self.queryset.filter(document__code=self.document_code)
        for item in table_header:
            label = item.get("name").get(self.lang, None)
            self.output["header"].append(label)
        for record in self.queryset:
            self.row = []
            for code in self.order_indicators_code:
                self.set_row(record, code)
            if self.status:
                self.status = self.get_status(record)
            author = record.author.first_name + " " + record.author.last_name
            self.output["body"].append({"row": self.row, "status": self.status, "id": record.id, "author": author})
        return self.output

    def get_status(self, record):
        last_status = record.history.last()
        if last_status:
            record_status = last_status.status_list.short_name.get(self.lang, None)
            comment = last_status.status_comment
            stage = last_status.stage
            created_at = last_status.created_at
            return {"name": record_status,
                    "comment": comment,
                    "stage": stage,
                    "created_at": created_at.strftime("%Y-%m-%d %H:%M:%S")}

    def table_header(self):
        ordering = Case(  # подзапрос для сохранения порядка
            *[When(code=code, then=pos) for pos, code in enumerate(self.order_indicators_code)],
            output_field=IntegerField())

        header = DcmIndicators.objects.filter(code__in=self.order_indicators_code,
                                              document__code=self.document_code).values("name").order_by(ordering)
        return header

    def set_row(self, record, code):
        value = record.record_values.filter(indicator__code=code).first()
        if not value:
            self.row.append(None)
            return
        if value.indicator.type_value in marker.reference:
            value = self.get_reference_value(value)
        else:
            value = value.value_int or value.value_str or \
                    value.value_text or value.value_datetime or \
                    value.value_bool or value.value_json or \
                    None

        self.row.append(value)

    def get_reference_value(self, value):
        """Получение значения по id из Справочника или Списка"""
        if value.indicator.type_value == 'dct':
            element = dct_models.Elements.objects.filter(id=value.value_reference).first()
            return element.short_name.get(self.lang, None)
        elif value.indicator.type_value == 'list':
            vl = stm_models.ListValues.objects.filter(id=value.value_reference).first()
            return vl.short_name.get(self.lang, None)
        return None


def table_present(queryset, params):
    """
    Представление данных в виде таблицы
    :header
    :body
    """
    try:
        ts = TableService(queryset, params)
        output = ts.construction_table()
    except Exception:
        return {"message": "Error"}
    return output
