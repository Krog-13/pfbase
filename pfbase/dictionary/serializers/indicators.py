from rest_framework import serializers
from ..models.indicators import DctIndicators


class IndicatorSerializer(serializers.ModelSerializer):
    class Meta:
        model = DctIndicators
        fields = "__all__"
