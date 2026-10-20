from django.utils import timezone
from django.utils.dateparse import parse_date

from ..system import models as stm_models

from django.db.models import Exists, OuterRef, Prefetch, Subquery
from .models.indicators import DcmIndicators
from .models.rivalues import RecordIndicatorValues
from .models.rhistory import RecordHistory
from .common import record_field


class RecordService:
    def __init__(self, filters):
        self.filters = filters
        self.document_code = filters["document_code"]
        self.indicators_code = filters["indicators_code"]
        self.stock_filters = filters.get("stock_filters", {})
        self.indicator_filters = filters.get("indicator_filters", {})
        self.indicators_code_list = []

    def prepare_records(self, qs):
        """Preparation records"""
        self.indicators_code_list = self.resolve_indicator_codes()
        records = self.prefetch_records(qs, self.indicators_code_list)
        if self.stock_filters:
            records = self.filter_by_stock(records)
        if self.indicator_filters:
            records = self.filter_by_indicator(records)
        return records

    def filter_by_stock(self, records):
        """Apply filters for built-in record fields."""
        for key, raw_value in self.stock_filters.items():
            value = raw_value.strip()
            if not value:
                continue
            if key == "NUMBER":
                records = records.filter(number__icontains=value)
            elif key == "CODE":
                records = records.filter(document__code=value)
            elif key in {"CREATED_AT", "DATE"}:
                dates = [part.strip() for part in value.split(",")]
                field = "created_at" if key == "CREATED_AT" else "date"
                if len(dates) == 2:
                    records = records.filter(**{f"{field}__date__range": dates})
                else:
                    records = records.filter(**{f"{field}__date": dates[0]})
            elif key == "AUTHOR_ID":
                author_id = int(value)
                records = records.filter(author_id=author_id)
            elif key == "ORGANIZATION_ID":
                organization_ids = [int(item.strip()) for item in value.split(",")]
                records = records.filter(organization_id__in=organization_ids)
        return records


    def filter_by_indicator(self, records):
        """Filter records by indicator code without multiplying joined rows."""
        # ToDo not filters Datetime, Time and range it
        indicators = DcmIndicators.objects.filter(
            document__code=self.document_code,
            code__in=self.indicator_filters,
        ).only("id", "code", "type_value", "is_multiple")
        indicators_by_code = {indicator.code: indicator for indicator in indicators}

        for code, raw_value in self.indicator_filters.items():
            indicator = indicators_by_code.get(code)
            field = record_field(indicator)
            if not field or not raw_value:
                continue
            value = self._coerce_value(indicator, raw_value)
            lookup = self.define_lookup(indicator, value)
            matching_values = RecordIndicatorValues.objects.filter(
                record_id=OuterRef("pk"), indicator_id=indicator.pk,
                **{f"{field}__{lookup}": value})
            records = records.filter(Exists(matching_values))
        return records

    @staticmethod
    def define_lookup(indicator, value):
        lookup = "exact"
        if indicator.type_value == "date":
            if isinstance(value, list):
                lookup = "date__range"
        elif indicator.is_multiple:
            lookup = "overlap"
        elif indicator.type_value in ("str", "text"):
            lookup = "icontains"
        return lookup

    @staticmethod
    def _coerce_value(indicator, value):
        """Parse query-string values using the model field's conversion rules."""
        if indicator.is_multiple:
            return [value]
        if indicator.type_value == "bool":
            if value not in {"true", "false", "1", "0"}:
                raise ValueError
            return value in {"true", "1"}
        if indicator.type_value in ("date", "datetime"):
            if value.count(","):
                return value.split(",")
        return value

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
        except ValueError:
            return {"message": "Error by build table"}

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
                "id", "code", "short_name")}
        body = []
        for record in self.queryset:
            values_by_code = {
                value.indicator.code: value
                for value in record.prefetched_values}
            values = {
                code: self.serialize_value(values_by_code.get(code))
                for code in idc_code}
            current_status = statuses.get(record.current_status_id)
            status = None
            if current_status:
                status = {
                    "name": current_status.short_name.get(self.lang)
                    or current_status.short_name.get("ru"),
                    "code": current_status.code,
                    "created_at": record.current_status_at}
            author_name = " ".join(
                part for part in (record.author.first_name, record.author.last_name) if part
            ) or record.author.username
            body.append({
                "id": record.id,
                "number": record.number,
                "date": record.date,
                "author": author_name,
                "status": status,
                "values": values})
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
