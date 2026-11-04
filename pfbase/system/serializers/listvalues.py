from rest_framework import serializers
from ..models.listvalues import ListValues


class LValuesSerializer(serializers.ModelSerializer):

    class Meta:
        model = ListValues
        fields = "list", "code", "short_name", "full_name"
