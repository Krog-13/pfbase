from rest_framework import serializers
from ..models.indicators import DcmIndicators


class IndicatorSerializer(serializers.ModelSerializer):

    class Meta:
        model = DcmIndicators
        fields = ("short_name", "full_name", "description", "code", "type_value",
                  "type_extend", "is_multiple", "is_required", "is_filtered")
