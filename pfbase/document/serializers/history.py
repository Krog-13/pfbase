from rest_framework import serializers
from ..models.rhistory import RecordHistory


class RHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = RecordHistory
        fields = "__all__"
