from django.db import transaction
from collections import namedtuple
from pfbase.exception import WrongType
from datetime import datetime
from ..system import models as stm_models
from ..dictionary import models as dct_models
from .models import Records, DcmIndicators, Documents, RecordIndicatorValues, RecordHistory
from django.db.models import Case, When, IntegerField
from django.utils import timezone

Typing = namedtuple('Typing', ['int', 'float', 'str', 'text', 'datetime', 'bool', 'reference', 'json'])
marker = Typing(int="int", float="float", str="str", text="text", json='json',
                datetime=["datetime", "date", "time"], bool="bool", reference=["dct", "list", "dcm"])


class RecordService:

    def __init__(self):
        self.main = None
        self.subs = None
        self.number = None
        self.date = None
        self.document_id = None
        self.code = None
        self.status_id = None
        self.parent_id = None

    def validate_data(self, request_data):
        """Validation data"""
        self.main = request_data['main']
        self.subs = request_data.get('subs', [])
        self.number = self.main.get('number', '0000')
        self.date_string = self.main.get('date')
        self.document_id = self.main.get('document_id')
        self.code = self.main.get('code')
        self.status_id = self.main.get('status_id')
        self.parent_id = self.main.get('parent_id')
        self.main_indicators = self.main.get('indicators', [])

        if self.date_string:
            naive_datetime = datetime.strptime(self.date_string, "%Y-%m-%d %H:%M")
            self.date = timezone.make_aware(naive_datetime)
        else:
            self.date = timezone.now()

        if not self.document_id:
            if not self.code:
                raise WrongType("Invalid data")

    def sub_validate_data(self, request_data):
        """Validation data"""
        self.number = request_data.get('number', '0005')
        self.date_string = request_data.get('date')
        self.document_id = request_data.get('document_id')
        self.code = request_data.get('code')
        self.status_id = request_data.get('status_id')
        self.parent_id = request_data.get('parent_id')
        self.sub_indicators = request_data.get('indicators', [])

        if self.date_string:
            naive_datetime = datetime.strptime(self.date_string, "%Y-%m-%d %H:%M")
            self.date = timezone.make_aware(naive_datetime)
        else:
            self.date = timezone.now()

        if not self.document_id:
            if not self.code:
                raise WrongType("Invalid data")
        if self.document_id:
            self.document = Documents.objects.get(id=self.document_id)
        else:
            self.document = Documents.objects.get(code=self.code)

    def create_riv(self, record, indicator_values):
        for item in indicator_values:
            value = item['value']
            type_value = item['type']
            idc_id = item.get('id')
            idc_code = item.get('code')

            if type_value == marker.reference[1]:
                if not value.isdigit():
                    raise WrongType("Invalid type value")
                stm_models.ListValues.objects.get(id=value)
            elif type_value == marker.reference[0]:
                if not value.isdigit():
                    raise WrongType("Invalid type value")
                dct_models.Elements.objects.get(id=value)
            elif type_value == marker.reference[2]:
                if not value.isdigit():
                    raise WrongType("Invalid type value")
                Records.objects.get(id=value)
            if idc_id:
                indicator = DcmIndicators.objects.get(id=idc_id, type_value=type_value)
            else:
                indicator = DcmIndicators.objects.get(code=idc_code, type_value=type_value)

            rv = record.record_values.create(indicator=indicator)
            result = self.separate_value(rv, type_value, value)
            if not result:
                raise WrongType("Invalid type value")
            rv.save()
        return True

    @transaction.atomic
    def create_record_pack(self, user, request_data):
        """
        Create Record with sub records
        """
        self.validate_data(request_data)

        if self.document_id:
            main_document = Documents.objects.get(id=self.document_id)
        else:
            main_document = Documents.objects.get(code=self.code)
        parent_r = Records.objects.get(id=self.parent_id) if self.parent_id else None

        main_record = Records.objects.create(
            number=self.number,
            date=self.date,
            parent=parent_r,
            author=user,
            document=main_document)

        self.create_riv(main_record, self.main_indicators)
        if self.status_id:
            self.create_history(main_record, self.status_id, user)

        if not self.subs:
            return main_record

        for sub in self.subs:
            self.sub_validate_data(sub)
            for row in sub.get('indicators', []):
                sub_record = Records.objects.create(
                    number=self.number,
                    date=self.date,
                    parent=main_record,
                    author=user,
                    document=self.document)
                self.create_riv(sub_record, row)
                if status_id := sub.get('status_id'):
                    self.create_history(sub_record, status_id, user)
        return main_record

    @transaction.atomic
    def create_record_iv(self, user, validated_data):
        """
        Create Record with their Indicators
        """
        document_id = validated_data.get('document_id')
        code = validated_data.get('code')
        indicators = validated_data.get('indicators')
        parent_id = validated_data.get('parent_id')
        status_id = validated_data.get('status_id')
        if document_id:
            document = Documents.objects.get(id=document_id)
        else:
            document = Documents.objects.get(code=code)
        parent_r = Records.objects.get(id=parent_id) if parent_id else None
        record = Records.objects.create(
            number=validated_data.get('number'),
            date=validated_data.get('date'),
            parent=parent_r,
            author=user,
            organization_id=user.organization_id,
            document=document)

        if not indicators:
            return record
        self.create_riv(record, indicators)
        if status_id:
            self.create_history(record, status_id, user)
        return record

    def validate_update_data(self, request_data):
        main = request_data['main']

        self.number = main.get('number', None)
        self.date_string = main.get('date', None)
        self.record_id = main['record_id']
        self.status_id = main.get('status_id', None)
        self.main_indicators = main.get('indicators', [])

        if self.date_string:
            naive_datetime = datetime.strptime(self.date_string, "%Y-%m-%d %H:%M")
            self.date = timezone.make_aware(naive_datetime)
        else:
            self.date = None

    def validate_update_sub_data(self, sub):

        self.sub_number = sub.get('number', None)
        self.date_string = sub.get('date', None)
        self.sub_record_id = sub['record_id']
        self.sub_status_id = sub.get('status_id', None)
        self.sub_indicators = sub.get('indicators', [])

        if self.date_string:
            naive_datetime = datetime.strptime(self.date_string, "%Y-%m-%d %H:%M")
            self.sub_date = timezone.make_aware(naive_datetime)
        else:
            self.sub_date = None

    def record_update_iv(self, indicators, record):
        for indicator in indicators:
            type_value = indicator.get('type')
            code = indicator.get('code')
            id = indicator.get('id')
            try:
                rv = record.record_values.get(id=id, indicator__type_value=type_value)
            except RecordIndicatorValues.DoesNotExist:
                record_indicator = DcmIndicators.objects.get(code=code, type_value=type_value)
                rv = record.record_values.create(indicator=record_indicator)
            some_value = indicator.get('value')
            result = self.separate_value(rv, type_value, some_value)
            if not result:
                raise WrongType("Invalid type value")
            rv.save()
        return True

    def validate_records_update_data(self, records):
        self.records = records['records']

    def validate_record_update_data(self, record):
        self.record_id = record['record_id']
        self.number = record.get('number', None)
        self.date_string = record.get('date', None)
        self.indicators = record.get('indicators', [])
        self.status_id = record.get('status_id', None)
        self.comment = record.get('comment', None)

        if self.date_string:
            naive_datetime = datetime.strptime(self.date_string, "%Y-%m-%d %H:%M")
            self.date = timezone.make_aware(naive_datetime)
        else:
            self.date = None

    @transaction.atomic
    def update_records_list(self, user, request_data):
        """
        Update Record with their Indicators
        """
        self.validate_records_update_data(request_data)
        for record in self.records:
            self.validate_record_update_data(record)
            record = Records.objects.get(id=self.record_id)
            if self.number:
                record.number = self.number
            if self.date:
                record.date = self.date
            record.user = user
            record.save()

            self.record_update_iv(self.indicators, record)

            if self.status_id:
                self.create_history(record, self.status_id, user, self.comment)

    @transaction.atomic
    def update_record_pack(self, user, request_data):
        """
        Update Record with their Indicators
        """
        self.validate_update_data(request_data)
        record = Records.objects.get(id=self.record_id)
        if self.number:
            record.number = self.number
        if self.date:
            record.date = self.date
        record.user = user
        record.save()
        self.record_update_iv(self.main_indicators, record)
        subs = request_data.get('subs', [])
        if self.status_id:
            self.create_history(record, self.status_id, user)

        for sub in subs:
            self.validate_update_sub_data(sub)
            record = Records.objects.get(id=self.sub_record_id)
            if self.sub_number:
                record.number = self.sub_number
            if self.sub_date:
                record.date = self.sub_date
            record.user = user
            record.save()
            self.record_update_iv(self.sub_indicators, record)

            if self.sub_status_id:
                self.create_history(record, self.sub_status_id, user)
        return True

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

    def separate_value(self, record_iv, type_value, value):
        if type_value == marker.int:
            record_iv.value_int = value
        elif type_value == marker.float:
            record_iv.value_float = value
        elif type_value == marker.str:
            record_iv.value_str = value
        elif type_value == marker.text:
            record_iv.value_text = value
        elif type_value == marker.bool:
            record_iv.value_bool = value
        elif type_value in marker.reference:
            record_iv.value_reference = value
        elif type_value == marker.json:
            record_iv.value_json = value
        elif type_value in marker.datetime:
            date = self.give_date_format(value, type_value)
            if not date:
                return False
            record_iv.value_datetime = date
        else:
            return False
        return True

    @staticmethod
    def create_history(record, status_id, user, comment=None):
        record.history.create(status_id=status_id, author=user, comment=comment)

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


class TableService:

    def __init__(self, queryset, params, data):
        self.queryset = queryset
        self.params = params
        self.data = data
        self.output = {"header": [], "body": []}
        self.row = []
        self.status = None

    def construction_table(self):
        self.document_code = self.data.get('document_code')
        self.lang = self.params.get("lang", "ru")
        self.status = self.params.get('status', False)
        self.order_indicators_code = self.data.get('indicators_code')
        table_header = self.table_header()
        self.queryset = self.queryset.filter(document__code=self.document_code)
        for item in table_header:
            label = item.get("short_name").get(self.lang, "ru")
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
            status = last_status.status.short_name.get(self.lang, "ru")
            code = last_status.status.code
            created_at = last_status.created_at
            return {"name": status,
                    "code": code,
                    "created_at": created_at.strftime("%Y-%m-%d %H:%M:%S")}

    def table_header(self):
        ordering = Case(  # подзапрос для сохранения порядка
            *[When(code=code, then=pos) for pos, code in enumerate(self.order_indicators_code)],
            output_field=IntegerField())

        header = DcmIndicators.objects.filter(code__in=self.order_indicators_code,
                                              document__code=self.document_code).values("short_name").order_by(ordering)
        return header

    def set_row(self, record, code):
        value = record.record_values.filter(indicator__code=code).first()
        if not value:
            self.row.append(None)
            return
        if value.indicator.type_value in marker.reference:
            value = self.get_reference_value(value)
        else:
            value = value.value_int or value.value_str or value.value_float or \
                    value.value_text or value.value_datetime or \
                    value.value_bool or value.value_json or \
                    None

        self.row.append(value)

    def get_reference_value(self, value):
        """Получение значения по id из Справочника или Списка"""
        if value.indicator.type_value == 'dct':
            element = dct_models.Elements.objects.filter(id=value.value_reference).first()
            return element.short_name.get(self.lang, "ru")
        elif value.indicator.type_value == 'list':
            vl = stm_models.ListValues.objects.filter(id=value.value_reference).first()
            return vl.short_name.get(self.lang, "ru")
        return None


def table_present(queryset, params, data):
    """
    Представление данных в виде таблицы
    :header
    :body
    """
    try:
        ts = TableService(queryset, params, data)
        output = ts.construction_table()
    except KeyError:
        return {"message": "Error"}
    return output


class HistoryService:

    @transaction.atomic
    def create_record_history(self, user, validated_data):
        """
        Create Record with their Indicators
        """
        records = validated_data.get('records')
        for record in records:
            record_id = record.get("record_id")
            status_id = record.get("status_id")
            comment = record.get("comment")
            if record_id and status_id:
                RecordHistory.objects.create(
                    record_id=record_id,
                    status_id=status_id,
                    comment=comment,
                    action="update",
                    author=user)
        return True
