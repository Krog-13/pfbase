from ..models.rhistory import RecordHistory
from ..service import HistoryService
from rest_framework.exceptions import ValidationError
from rest_framework import serializers, exceptions
from datetime import timedelta
from django.utils.timezone import localtime


class RHistorySerializer(serializers.ModelSerializer):
    author = serializers.CharField(source="author.first_name")
    status = serializers.JSONField(source="status.short_name")
    created_at = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = RecordHistory
        fields = "__all__"

    def get_full_name(self, obj):
        return f"{obj.author.first_name} {obj.author.last_name}"

    def get_created_at(self, obj):
        # Delete if use Django setting timezone
        created = localtime(obj.created_at) + timedelta(hours=5)
        return created.strftime("%Y-%m-%d %H:%M:%S")

class HistoryPostSerializer(serializers.Serializer):
    record_id = serializers.IntegerField(required=True)
    status_id = serializers.IntegerField(required=True)
    comment = serializers.CharField(required=False, allow_null=True)

    def create(self, request_data):
        user = self.context['request'].user
        if not user:
            user = self.context['user']
        try:
            return HistoryService().create_history(user, request_data)
        except ValidationError as e:
            raise exceptions.ValidationError({"error": str(e)})
        except KeyError as e:
            raise exceptions.ValidationError({"error": str(e)})
        except Exception as e:
            raise exceptions.ValidationError({"error": str(e)})

class HistoryPackPostSerializer(serializers.Serializer):
    records = serializers.ListField(required=True)

    def create(self, request_data):
        user = self.context['request'].user
        if not user:
            user = self.context['user']
        try:
            return HistoryService().create_record_history(user, request_data)
        except ValidationError as e:
            raise exceptions.ValidationError({"error": str(e)})
        except KeyError as e:
            raise exceptions.ValidationError({"error": str(e)})
        except Exception as e:
            raise exceptions.ValidationError({"error": str(e)})
