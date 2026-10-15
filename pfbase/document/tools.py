from django.utils import timezone

from ..system import models as stm_models
from .models import DcmIndicators


class TableService:
    def __init__(self, queryset, params, document_code, indicator_codes):
        self.queryset = queryset
        self.params = params
        self.document_code = document_code
        self.indicator_codes = indicator_codes
        self.lang = params.get("lang", "ru")

    def construction_table(self):
        header = self.set_header()

        status_ids = {
            record.current_status_id
            for record in self.queryset
            if record.current_status_id is not None
        }
        statuses = {
            item.id: item
            for item in stm_models.ListValues.objects.filter(id__in=status_ids).only(
                "id", "code", "short_name"
            )
        }

        body = self.set_body(statuses)
        return {"header": header, "body": body}

    def set_header(self):
        indicators = list(
            DcmIndicators.objects.filter(
                document__code=self.document_code,
                code__in=self.indicator_codes
            )
        )
        indicators_by_code = {indicator.code: indicator for indicator in indicators}
        missing_codes = [code for code in self.indicator_codes if code not in indicators_by_code]
        if missing_codes:
            raise ValueError(f"Unknown indicators for document: {', '.join(missing_codes)}")
        header = [
            {
                "code": indicators_by_code[code].code,
                "label": indicators_by_code[code].short_name or {},
                "type": indicators_by_code[code].type_value,
                "is_multiple": indicators_by_code[code].is_multiple,
            }
            for code in self.indicator_codes
        ]
        return header

    def set_body(self, statuses):
        body = []
        for record in self.queryset:
            values_by_code = {
                value.indicator.code: value
                for value in record.prefetched_values
            }
            values = {
                code: self.serialize_value(values_by_code.get(code))
                for code in self.indicator_codes
            }
            current_status = statuses.get(record.current_status_id)
            status = None
            if current_status:
                status = {
                    "name": current_status.short_name.get(self.lang)
                    or current_status.short_name.get("ru"),
                    "code": current_status.code,
                    "created_at": record.current_status_at,
                }
            author_name = " ".join(
                part for part in (record.author.first_name, record.author.last_name) if part
            ) or record.author.username
            body.append({
                "id": record.id,
                "number": record.number,
                "date": record.date,
                "author": author_name,
                "status": status,
                "values": values,
            })
        return body

    def serialize_value(self, value):
        if not value:
            return None
        kind = value.indicator.type_value
        if value.indicator.is_multiple:
            if kind in ("dct", "dcm", "list", "user", "org", "list_integers", "list_string"):
                return value.value_array_int
            return value.value_array_str

        if kind in ("dct", "dcm", "user", "list", "org"):
            return value.value_reference

        if kind in ("datetime", "date", "time"):
            date_value = value.value_datetime
            if date_value is None:
                return None
            if timezone.is_aware(date_value):
                date_value = timezone.localtime(date_value)
            formats = {
                "datetime": "%Y-%m-%d %H:%M",
                "date": "%Y-%m-%d",
                "time": "%H:%M",
            }
            return date_value.strftime(formats[kind])

        field_by_type = {
            "str": "value_str", "file": "value_str", "int": "value_int",
            "float": "value_float", "bool": "value_bool", "text": "value_text",
            "json": "value_json",
            "list_integers": "value_array_int", "list_strings": "value_array_str",
        }
        field = field_by_type.get(kind)
        return getattr(value, field) if field else None


def build_records_table(queryset, params, document_code, indicator_codes):
    """Build a localized header and a page of record rows."""
    try:
        return TableService(queryset, params, document_code, indicator_codes).construction_table()
    except ValueError as error:
        return {"message": str(error)}
