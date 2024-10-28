from rest_framework import serializers
from ..models.rivalues import RecordIndicatorValues


class RIValuesSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecordIndicatorValues
        fields = "__all__"
