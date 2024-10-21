from rest_framework import serializers, exceptions
from rest_framework.exceptions import ValidationError

from ..models.records import Records
from ..models.rivalues import RecordIndicatorValues
from pfbase.dictionary.models.elements import Elements
from pfbase.system.models.listvalues import ListValues
from ..service import RecordService


class RecordSerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()

    class Meta:
        model = Records
        fields = "__all__"

    def get_children(self, obj):
        children_qs = obj.children.all()
        if children_qs.exists():
            return True
        return False


class RIValueSerializer(serializers.ModelSerializer):
    value_name = serializers.SerializerMethodField()
    indicator = serializers.CharField(source='indicator.name')
    type_value = serializers.CharField(source='indicator.type_value')

    class Meta:
        model = RecordIndicatorValues
        fields = 'indicator', 'type_value', 'value_int', 'value_str', 'value_text', 'value_datetime',\
            'value_bool', 'value_reference', 'value_name',

    def get_value_name(self, obj):
        if obj.indicator.type_value == 'dct':
            element = Elements.objects.filter(id=obj.value_reference).first()
            return element.short_name
        elif obj.indicator.type_value == 'enum':
            record = ListValues.objects.filter(id=obj.value_reference).first()
            return record.short_name


class RIGetSerializer(serializers.ModelSerializer):
    indicator_value = RIValueSerializer(source="record_values", many=True, read_only=True)
    children = serializers.SerializerMethodField()

    class Meta:
        model = Records
        fields = '__all__'

    def get_children(self, obj):
        children_qs = obj.children.all()
        if children_qs.exists():
            return True
        return False


class CommonSerializer(serializers.Serializer):
    def to_internal_value(self, data):
        # Get all allowed fields
        allowed_fields = set(self.fields.keys())
        # Get the fields actually passed in the request
        received_fields = set(data.keys())

        # Check for unknown fields
        unknown_fields = received_fields - allowed_fields
        if unknown_fields:
            raise exceptions.ValidationError({"unknown_fields": f"Unknown field(s): {', '.join(unknown_fields)}"})
        return super().to_internal_value(data)


class IndicatorSerializer(CommonSerializer):
    id = serializers.IntegerField()
    code = serializers.CharField(max_length=50, required=False)
    value = serializers.CharField(max_length=100)
    type = serializers.CharField(max_length=10)


class RecordPostSerializer(CommonSerializer):
    number = serializers.CharField(required=False, default="0000")
    date = serializers.DateField(required=False)
    document_id = serializers.IntegerField(required=True)
    parent_id = serializers.IntegerField(required=False)
    indicators = IndicatorSerializer(many=True, required=False)

    def create(self, validated_data):
        user = self.context['request'].user
        try:
            return RecordService().create_record_iv(user, validated_data)
        except ValidationError as e:
            raise exceptions.ValidationError({"error": str(e)})


class RecordUpdateSerializer(CommonSerializer):
    number = serializers.CharField(required=False)
    date = serializers.DateField(required=False)
    parent_id = serializers.IntegerField(required=False)
    indicators = IndicatorSerializer(many=True, required=False)

    def update(self, instance, validated_data):
        user = self.context['request'].user
        try:
            return RecordService().update_record_iv(instance, user, validated_data)
        except ValidationError as e:
            raise exceptions.ValidationError({"error": str(e)})
