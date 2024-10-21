from rest_framework import serializers
from ..models.RIValues import RIValues


class RIValuesSerializer(serializers.ModelSerializer):
    class Meta:
        model = RIValues
        fields = "__all__"
