from ..models.rhistory import RecordHistory
from ..service import HistoryService
from rest_framework.exceptions import ValidationError
from rest_framework import serializers, exceptions


class RHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = RecordHistory
        fields = "__all__"


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
