"""
Serializers for the models in the pfbase app
"""
from rest_framework import serializers
from .models import DctIndicator, ElementIndicatorValue, ABCDictionary, Element, ElementHistory, \
    RecordIndicatorValue, ABCDocument, Record, DcmIndicator, RecordHistory, PFEnum, Notification, User


# serializers for Dictionary
class DictionarySerializer(serializers.ModelSerializer):
    class Meta:
        model = ABCDictionary
        fields = "__all__"


class DctIndicatorSerializer(serializers.ModelSerializer):
    class Meta:
        model = DctIndicator
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


# serializers for Documents
class ABCDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ABCDocument
        fields = "__all__"


class DcmIndicatorSerializer(serializers.ModelSerializer):
    class Meta:
        model = DcmIndicator
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


# serializers for System
class PFEnumSerializer(serializers.ModelSerializer):
    class Meta:
        model = PFEnum
        fields = "__all__"


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = "__all__"


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = "__all__"
