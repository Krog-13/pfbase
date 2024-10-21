from rest_framework import serializers
from ..models.indicators import DcmIndicators


class IndicatorSerializer(serializers.ModelSerializer):
    class Meta:
        model = DcmIndicators
        fields = "__all__"
