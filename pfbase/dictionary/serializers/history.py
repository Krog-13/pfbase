from rest_framework import serializers
from ..models.ehistory import ElementHistory


class EHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ElementHistory
        fields = "__all__"
