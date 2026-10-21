from django.db.models import Prefetch
from .models.rhistory import RecordHistory
from .models.records import Records

STOCK_FILTER_KEYS = {
    "NUMBER", "CODE", "CREATED_AT", "DATE", "AUTHOR_ID", "ORGANIZATION_ID", "STATUS_ID",
}

record_type_mapping = {
    "str": "value_str",
    "text": "value_text",
    "int": "value_int",
    "float": "value_float",
    "bool": "value_bool",
    "json": "value_json",
    "file": "value_str",
    "datetime": "value_datetime",
    "date": "value_datetime",
    "time": "value_datetime",
    "dct": "value_reference",
    "dcm": "value_reference",
    "list": "value_reference",
    "user": "value_reference",
    "org": "value_reference",
    "list_integers": "value_array_int",
    "list_string": "value_array_str"
}

multiple_type_mapping = {
    "value_array_int": ("dct", "dcm", "user", "org", "list_integers"),
    "value_array_str": ("str", "file", "datetime", "date", "time", "list_string")}

def record_field(indicator):
    if indicator.is_multiple:
        if indicator.type_value in multiple_type_mapping["value_array_int"]:
            return "value_array_int"
        elif indicator.type_value in multiple_type_mapping["value_array_str"]:
            return "value_array_str"
        return None
    else:
        return record_type_mapping.get(indicator.type_value)



def get_record_detail(record_id):
    """Fetch one visible record with relations used by its detail serializer."""
    return Records.objects.filter(is_deleted=False).select_related(
        "document", "author", "organization", "parent"
    ).prefetch_related(
        "record_values__indicator",
        Prefetch(
            "history",
            queryset=RecordHistory.objects.select_related("status").order_by("-created_at", "-id"),
            to_attr="prefetched_history",
        ),
    ).filter(pk=record_id).first()






