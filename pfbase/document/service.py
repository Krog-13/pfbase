from django.db import transaction
from collections import namedtuple
from pfbase.exception import WrongType
from django.utils import timezone
from datetime import datetime
from ..system import models as stm_models
from ..dictionary import models as dct_models
from .models import Records, DcmIndicators, Documents
from django.db.models import Case, When, IntegerField

Typing = namedtuple('Typing', ['int', 'float', 'str', 'text', 'datetime', 'bool', 'reference', 'json'])
marker = Typing(int="int", float="float", str="str", text="text", json='json', datetime=["datetime", "date", "time"],
                bool="bool", reference=["dct", "list"])


class RecordService:

    @transaction.atomic
    def create_record_pack(self, user, validated_data):
        """
        Create Record with sub records
        """
        main = validated_data.get('main')
        sub = validated_data.get('sub')
        status = main.get('status')
        main_indicators = main.get('indicators')
        sub_indicators = sub.get('indicators')
        document_id = main.get('document_id')
        parent_id = main.get('parent_id')
        sub_document_id = sub.get('document_id')
        code = main.get('code')
        sub_code = sub.get('code')
        if document_id:
            document = Documents.objects.get(id=document_id)
        else:
            document = Documents.objects.get(code=code)
        if sub_document_id:
            sub_document = Documents.objects.get(id=sub_document_id)
        else:
            sub_document = Documents.objects.get(code=sub_code)
        parent_r = Records.objects.get(id=parent_id) if parent_id else None

        main_record = Records.objects.create(
            number=main.get('number'),
            date=main.get('date'),
            parent=parent_r,
            author=user,
            document=document)

        for pack_idc in sub_indicators:
            record = Records.objects.create(
                number=sub.get('number', "0000"),
                date=sub.get('date', datetime.today()),
                parent=main_record,
                author=user,
                document=sub_document)

            for indicator in pack_idc:
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
                    dct_models.Elements.objects.get(id=some_value)
                if idc_id:
                    dcm_indicator = DcmIndicators.objects.get(id=idc_id, type_value=type_value)
                else:
                    dcm_indicator = DcmIndicators.objects.get(code=idc_code, type_value=type_value)
                rv = record.record_values.create(indicator=dcm_indicator)
                result = self.separate_value(rv, type_value, some_value)
                if not result:
                    raise WrongType("Invalid type value")
                rv.save()
        if status:
            self.create_history(main_record, status, user)
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
        status = validated_data.get('status')
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
            document=document)

        if not indicators:
            return record
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
                dct_models.Elements.objects.get(id=some_value)
            if idc_id:
                dcm_indicator = DcmIndicators.objects.get(id=idc_id, type_value=type_value)
            else:
                dcm_indicator = DcmIndicators.objects.get(code=idc_code, type_value=type_value)
            rv = record.record_values.create(indicator=dcm_indicator)
            result = self.separate_value(rv, type_value, some_value)
            if not result:
                raise WrongType("Invalid type value")
            rv.save()
        if status:
            self.create_history(record, status, user)
        return record

    def create_history(self, record, status, user):
        status_id = status.get("status_id")
        record.history.create(
            status_id=status_id,
            author=user)

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

    def __init__(self, queryset, params, data):
        self.queryset = queryset
        self.params = params
        self.data = data
        self.output = {"header": [], "body": []}
        self.row = []
        self.status = None

    def construction_table(self):
        self.document_code = self.data.get('document_code')
        self.lang = self.params.get('lang')
        self.status = self.params.get('status', False)
        self.order_indicators_code = self.data.get('indicators_code')
        table_header = self.table_header()
        self.queryset = self.queryset.filter(document__code=self.document_code)
        for item in table_header:
            label = item.get("short_name").get(self.lang, None)
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
            status = last_status.status.short_name.get(self.lang, None)
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
            return element.short_name.get(self.lang, None)
        elif value.indicator.type_value == 'list':
            vl = stm_models.ListValues.objects.filter(id=value.value_reference).first()
            return vl.short_name.get(self.lang, None)
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
    except Exception:
        return {"message": "Error"}
    return output
