from rest_framework import serializers
from ..models.eivalues import ElementIndicatorValues


class EIValuesSerializer(serializers.ModelSerializer):
    class Meta:
        model = ElementIndicatorValues
        fields = "__all__"
