from rest_framework import serializers
from ..models.listvalues import ListValues


class LValuesSerializer(serializers.ModelSerializer):
    class Meta:
        model = ListValues
        fields = "__all__"
