from django.db.models import Exists, OuterRef, Prefetch, Subquery
from django.utils.dateparse import parse_date
from .models.indicators import DcmIndicators
from .models.rivalues import RecordIndicatorValues
from .models.rhistory import RecordHistory
from .models.records import Records


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






