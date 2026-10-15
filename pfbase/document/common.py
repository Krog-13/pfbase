from django.db.models import OuterRef, Prefetch, Subquery
from .models.indicators import DcmIndicators
from .models.rivalues import RecordIndicatorValues
from .models.rhistory import RecordHistory


def prepare_records(qs, document_code, indicator_codes):
    indicator_ids = list(
        DcmIndicators.objects.filter(
            document__code=document_code,
            code__in=indicator_codes,
        ).values_list("id", flat=True)
    )
    # ToDo query time check
    values_queryset = RecordIndicatorValues.objects.filter(
        indicator_id__in=indicator_ids
    ).select_related("indicator")
    latest_history = RecordHistory.objects.filter(
        record_id=OuterRef("pk")
    ).order_by("-created_at", "-id")
    records = qs.filter(document__code=document_code).select_related("author").prefetch_related(
        Prefetch("record_values", queryset=values_queryset, to_attr="prefetched_values"),
    ).annotate(
        current_status_id=Subquery(latest_history.values("status_id")[:1]),
        current_status_at=Subquery(latest_history.values("created_at")[:1]),
    )
    return records
