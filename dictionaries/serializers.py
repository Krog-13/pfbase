from rest_framework import serializers
from IEF.base_model import Enum
from .models import Indicator, ElementIndicatorValue, ABCDictionary, Element, ElementHistory


class DictionarySerializer(serializers.ModelSerializer):
    class Meta:
        model = ABCDictionary
        fields = "__all__"


class IndicatorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Indicator
        fields = "__all__"


class EIValueSerializer(serializers.ModelSerializer):
    class Meta:
        model = ElementIndicatorValue
        fields = "__all__"


class ElementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Element
        fields = "__all__"


class ElementHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ElementHistory
        fields = "__all__"


class EnumSerializer(serializers.ModelSerializer):
    class Meta:
        model = Enum
        fields = "__all__"
