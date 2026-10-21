from rest_framework import serializers
from django.utils import timezone


class RecordQuerySerializer(serializers.Serializer):
    document_code = serializers.CharField()
    indicators_code = serializers.ListField(child=serializers.CharField(),
                                            required=False,
                                            default=list)

class RecordRetrieveSerializer(serializers.Serializer):
    """Build the detail response directly without relying on other serializers."""

    reference_types = {"dct", "list", "dcm", "user", "org"}

    def to_representation(self, record):
        values = list(record.record_values.all())
        history = self._get_latest_history(record)

        status_value = history.status if history else None
        organization = record.organization
        return {
            "id": record.pk,
            "number": record.number,
            "date": record.date,
            "active": record.active,
            "document": record.document_id,
            "code": record.document.code if record.document else None,
            "parent": record.parent_id,
            "author": record.author_id,
            "organization": record.organization_id,
            "is_deleted": record.is_deleted,
            "created_at": record.created_at,
            "updated_at": record.updated_at,
            "deleted_at": record.deleted_at,
            "indicator_value": [
                self._serialize_indicator_value(value)
                for value in values
            ],
            "status": status_value.short_name if status_value else None,
            "status_info": {
                "code": status_value.code if status_value else None,
                "comment": history.comment,
            } if history else None,
            "children": record.children.exists(),
            "organization_detail": {
                "id": record.organization_id,
                "short_name": organization.short_name if organization else None,
            },
        }

    @staticmethod
    def _get_latest_history(record):
        prefetched_history = getattr(record, "prefetched_history", None)
        if prefetched_history is not None:
            return prefetched_history[0] if prefetched_history else None
        return record.history.select_related("status").order_by("-created_at", "-id").first()

    def _serialize_indicator_value(self, value):
        indicator = value.indicator
        kind = indicator.type_value
        is_multiple = indicator.is_multiple

        if is_multiple:
            serialized_value = value.value_array_int if kind in self.reference_types else value.value_array_str
        elif kind in self.reference_types:
            serialized_value = value.value_reference
        elif kind in {"datetime", "date", "time"}:
            serialized_value = self._format_datetime(value.value_datetime, kind)
        else:
            field_by_type = {
                "str": "value_str",
                "text": "value_text",
                "int": "value_int",
                "float": "value_float",
                "json": "value_json",
                "file": "value_str",
                "bool": "value_bool",
                "list_integers": "value_array_int",
                "list_string": "value_array_str",
                "list_strings": "value_array_str",
            }
            field = field_by_type.get(kind)
            serialized_value = getattr(value, field) if field else None

        return {
            "id": value.pk,
            "short_name": indicator.short_name,
            "full_name": indicator.full_name,
            "code": indicator.code,
            "type_value": kind,
            "type_extend": indicator.type_extend,
            "is_multiple": is_multiple,
            "value_reference": value.value_reference,
            "value_array_int": value.value_array_int,
            "value_array_str": value.value_array_str,
            "value": serialized_value,
        }

    @staticmethod
    def _format_datetime(value, kind):
        if not value:
            return None
        if timezone.is_aware(value):
            value = timezone.localtime(value)
        formats = {
            "datetime": "%Y-%m-%d %H:%M",
            "date": "%Y-%m-%d",
            "time": "%H:%M",
        }
        return value.strftime(formats[kind])