"""
Serializers for the models in the pfbase app
"""
from rest_framework import serializers, exceptions
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


# common serializers
class IndicatorPostSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=50)
    value = serializers.CharField(max_length=100)
    type = serializers.CharField(max_length=10)


class IndicatorUpdateSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    value = serializers.CharField(max_length=100)
    type = serializers.CharField(max_length=10)


# Custom dictionary serializer
class EIndicatorValueSerializer(serializers.ModelSerializer):
    value_name = serializers.SerializerMethodField()
    indicator = serializers.CharField(source='indicator.name')
    type_value = serializers.CharField(source='indicator.type_value')

    class Meta:
        model = ElementIndicatorValue
        fields = 'indicator', 'type_value', 'value_int', 'value_str', 'value_text', 'value_datetime',\
            'value_bool', 'value_reference', 'value_name',

    def get_value_name(self, obj):
        if obj.indicator.type_value == 'dct':
            element = Element.objects.get(id=obj.value_reference)
            return element.short_name


class EIGetSerializer(serializers.ModelSerializer):
    element_value = EIndicatorValueSerializer(many=True, read_only=True)

    class Meta:
        model = Element
        fields = 'short_name', 'full_name', 'code', 'parent', 'element_value'


class EMetadataPostSerializer(serializers.Serializer):
    short_name = serializers.JSONField()
    full_name = serializers.JSONField(required=False)
    code = serializers.CharField(max_length=50)
    dictionary = serializers.CharField(max_length=50)
    parent_id = serializers.IntegerField(required=False)
    indicators = IndicatorPostSerializer(many=True, required=False)

    def to_internal_value(self, data):
        # Get all allowed fields
        allowed_fields = set(self.fields.keys())
        # Get the fields actually passed in the request
        received_fields = set(data.keys())

        # Check for unknown fields
        unknown_fields = received_fields - allowed_fields
        if unknown_fields:
            raise exceptions.ValidationError(f"Unknown field: {', '.join(unknown_fields)}")
        return super().to_internal_value(data)


class EMetadataUpdateSerializer(serializers.Serializer):
    short_name = serializers.JSONField(required=False)
    full_name = serializers.JSONField(required=False)
    code = serializers.CharField(max_length=50, required=False)
    parent_id = serializers.IntegerField(required=False)
    indicators = IndicatorUpdateSerializer(many=True, required=False)

    def to_internal_value(self, data):
        # Get all allowed fields
        allowed_fields = set(self.fields.keys())
        # Get the fields actually passed in the request
        received_fields = set(data.keys())

        # Check for unknown fields
        unknown_fields = received_fields - allowed_fields
        if unknown_fields:
            raise exceptions.ValidationError(f"Unknown field(s): {', '.join(unknown_fields)}")
        return super().to_internal_value(data)


class EIPostSerializer(serializers.Serializer):
    metadata = EMetadataPostSerializer()


class EIUpdateSerializer(serializers.Serializer):
    metadata = EMetadataUpdateSerializer()

    class Meta:
        extra_kwargs = None


# Custom document serializer
class RIndicatorValueSerializer(serializers.ModelSerializer):
    value_name = serializers.SerializerMethodField()
    indicator = serializers.CharField(source='indicator.name')
    type_value = serializers.CharField(source='indicator.type_value')

    class Meta:
        model = RecordIndicatorValue
        fields = 'indicator', 'type_value', 'value_int', 'value_str', 'value_text', 'value_datetime',\
            'value_bool', 'value_reference', 'value_name',

    def get_value_name(self, obj):
        if obj.indicator.type_value == 'dct':
            element = Element.objects.get(id=obj.value_reference)
            return element.short_name


class RMetadataPostSerializer(serializers.Serializer):
    number = serializers.CharField(required=False)
    date = serializers.DateField(required=False)
    document = serializers.CharField(max_length=50)
    parent_id = serializers.IntegerField(required=False)
    indicators = IndicatorPostSerializer(many=True)

    def to_internal_value(self, data):
        # Get all allowed fields
        allowed_fields = set(self.fields.keys())
        # Get the fields actually passed in the request
        received_fields = set(data.keys())

        # Check for unknown fields
        unknown_fields = received_fields - allowed_fields
        if unknown_fields:
            raise exceptions.ValidationError(f"Unknown field: {', '.join(unknown_fields)}")
        return super().to_internal_value(data)


class RMetadataUpdateSerializer(serializers.Serializer):
    number = serializers.CharField(required=False)
    date = serializers.DateField(required=False)
    parent_id = serializers.IntegerField(required=False)
    indicators = IndicatorUpdateSerializer(many=True, required=False)

    def to_internal_value(self, data):
        # Get all allowed fields
        allowed_fields = set(self.fields.keys())
        # Get the fields actually passed in the request
        received_fields = set(data.keys())

        # Check for unknown fields
        unknown_fields = received_fields - allowed_fields
        if unknown_fields:
            raise exceptions.ValidationError(f"Unknown field: {', '.join(unknown_fields)}")
        return super().to_internal_value(data)


class RIPostSerializer(serializers.Serializer):
    metadata = RMetadataPostSerializer()


class RIUpdateSerializer(serializers.Serializer):
    metadata = RMetadataUpdateSerializer()


class RIGetSerializer(serializers.ModelSerializer):
    record_value = RIndicatorValueSerializer(many=True, read_only=True)

    class Meta:
        model = Record
        fields = 'number', 'date', 'created_at', 'parent', 'record_value'
