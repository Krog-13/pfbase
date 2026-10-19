from django.utils import timezone

from ..system import models as stm_models

from django.db.models import OuterRef, Prefetch, Subquery
from .models.indicators import DcmIndicators
from .models.rivalues import RecordIndicatorValues
from .models.rhistory import RecordHistory


class RecordService:
    def __init__(self, filters):
        self.filters = filters
        self.document_code = filters["document_code"]
        self.indicators_code = filters["indicators_code"]
        self.indicators_code_list = []

    def prepare_records(self, qs):
        """Preparation records"""
        self.indicators_code_list = self.resolve_indicator_codes()
        records = self.prefetch_records(qs, self.indicators_code_list)
        return records

    def resolve_indicator_codes(self):
        """Return requested indicator codes, or all codes when none were supplied."""
        indicator_codes = list(dict.fromkeys(
            code.strip()
            for raw_code in self.indicators_code
            for code in raw_code.split(",") if code.strip()))
        if indicator_codes:
            return indicator_codes
        return list(
            DcmIndicators.objects.filter(document__code=self.document_code)
            .order_by("index_sort", "id")
            .values_list("code", flat=True))

    def prefetch_records(self, qs, indicator_codes):
        """Build the records queryset, prefetch requested values, and apply filters."""
        indicator_ids = list(
            DcmIndicators.objects.filter(
                document__code=self.document_code,
                code__in=indicator_codes,
            ).values_list("id", flat=True))
        # ToDo query time check
        values_queryset = RecordIndicatorValues.objects.filter(
            indicator_id__in=indicator_ids
        ).select_related("indicator")
        latest_history = RecordHistory.objects.filter(
            record_id=OuterRef("pk")
        ).order_by("-created_at", "-id")
        records = qs.filter(
            document__code=self.document_code,
        ).select_related("author").prefetch_related(
            Prefetch("record_values", queryset=values_queryset, to_attr="prefetched_values"),
        ).annotate(
            current_status_id=Subquery(latest_history.values("status_id")[:1]),
            current_status_at=Subquery(latest_history.values("created_at")[:1]))
        return records

    def build_records_table(self, queryset):
        """Build a localized header and a page of record rows."""
        try:
            ts = TableService(queryset)
            table = ts.construction_table(self.document_code,
                                          self.indicators_code_list)
            return table
        except ValueError as error:
            return {"message": str(error)}

class TableService:
    def __init__(self, queryset):
        self.queryset = queryset
        self.lang = "ru"

    def construction_table(self, dcm_code, idc_code):
        header = self.set_header(dcm_code, idc_code)
        body = self.set_body(idc_code)
        return {"header": header, "body": body}

    def set_header(self, dcm_code, idc_code):
        indicators = list(
            DcmIndicators.objects.filter(
                document__code=dcm_code, code__in=idc_code))
        indicators_by_code = {indicator.code: indicator for indicator in indicators}
        missing_codes = [code for code in idc_code if code not in indicators_by_code]
        if missing_codes:
            raise ValueError(f"Unknown indicators for document: {', '.join(missing_codes)}")
        header = [
            {
                "code": indicators_by_code[code].code,
                "label": indicators_by_code[code].short_name or {},
                "type": indicators_by_code[code].type_value,
                "is_multiple": indicators_by_code[code].is_multiple,
            }
            for code in idc_code
        ]
        return header

    def set_body(self, idc_code):
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
        body = []
        for record in self.queryset:
            values_by_code = {
                value.indicator.code: value
                for value in record.prefetched_values
            }
            values = {
                code: self.serialize_value(values_by_code.get(code))
                for code in idc_code
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

    @staticmethod
    def serialize_value(value):
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
