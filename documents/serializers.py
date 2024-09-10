from rest_framework import serializers
from .models import RecordIndicatorValue, ABCDocument, Record, Indicator, RecordHistory


class ABCDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ABCDocument
        fields = "__all__"


class IndicatorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Indicator
        fields = "__all__"


class RecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = Record
        fields = "__all__"


class RIValueSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecordIndicatorValue
        fields = "__all__"


class RecordHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = RecordHistory
        fields = "__all__"
