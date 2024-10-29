from rest_framework import serializers, exceptions
from rest_framework.exceptions import ValidationError
from ..models.records import Records
from ..models.rivalues import RecordIndicatorValues
from pfbase.dictionary.models.elements import Elements
from pfbase.system.models.listvalues import ListValues
from ..service import RecordService
import datetime


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
    short_name = serializers.JSONField(source='indicator.short_name')
    type_value = serializers.CharField(source='indicator.type_value')
    type_extend = serializers.CharField(source='indicator.type_extend')
    value = serializers.SerializerMethodField()

    class Meta:
        model = RecordIndicatorValues
        fields = 'id', 'short_name', 'type_value', 'type_extend', 'value_reference', 'value'

    def get_value_name(self, obj):
        if obj.indicator.type_value == 'dct':
            element = Elements.objects.filter(id=obj.value_reference).first()
            return element.short_name
        elif obj.indicator.type_value == 'list':
            record = ListValues.objects.filter(id=obj.value_reference).first()
            return record.short_name

    def get_value(self, obj):
        value_fields = [
            'value_int', 'value_text', 'value_datetime', 'value_float',
            'value_bool', 'value_str', 'value_json']
        for field in value_fields:
            if obj.indicator.type_value in ['dct', 'list']:
                return self.get_value_name(obj)
            if value := getattr(obj, field, None):
                return value
        return None


class RIGetSerializer(serializers.ModelSerializer):
    indicator_value = RIValueSerializer(source="record_values", many=True, read_only=True)
    status = serializers.SerializerMethodField()
    children = serializers.SerializerMethodField()

    class Meta:
        model = Records
        fields = '__all__'

    def get_status(self, obj):
        last_status = obj.history.last()
        if last_status:
            return last_status.status_list.short_name
        return None

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
    value = serializers.CharField(max_length=100, required=False, allow_null=True)
    type = serializers.CharField(max_length=10)


class RecordPostSerializer(CommonSerializer):
    number = serializers.CharField(required=False, default="0000")
    date = serializers.DateTimeField(required=False, default=datetime.datetime.now())
    document_id = serializers.IntegerField(required=True)
    parent_id = serializers.IntegerField(required=False)
    indicators = IndicatorSerializer(many=True, required=False)
    status_id = serializers.IntegerField(required=False)

    def create(self, validated_data):

        user = self.context['request'].user
        if not user:
            user = self.context['user']
        try:
            return RecordService().create_record_iv(user, validated_data)
        except ValidationError as e:
            raise exceptions.ValidationError({"error": str(e)})


class RecordPackPostSerializer(serializers.Serializer):
    main = serializers.JSONField(required=True)
    sub = serializers.JSONField(required=True)

    def create(self, validated_data):
        user = self.context['request'].user
        if not user:
            user = self.context['user']
        try:
            return RecordService().create_record_pack(user, validated_data)
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


class RIValueSerializer1(serializers.ModelSerializer):
    value = serializers.SerializerMethodField()

    class Meta:
        model = RecordIndicatorValues
        fields = 'value',

    def get_value_name(self, obj):
        if obj.indicator.type_value == 'dct':
            element = Elements.objects.filter(id=obj.value_reference).first()
            return element.short_name
        elif obj.indicator.type_value == 'list':
            record = ListValues.objects.filter(id=obj.value_reference).first()
            return record.short_name

    def get_value(self, obj):
        value_fields = [
            'value_int', 'value_text', 'value_datetime',
            'value_bool', 'value_reference', 'value_str', 'value_json']
        for field in value_fields:
            if obj.indicator.type_value in ['dct', 'list']:
                return self.get_value_name(obj)
            if value := getattr(obj, field, None):
                return value
        return None


class RIListSerializer(serializers.ModelSerializer):
    indicator_value = RIValueSerializer1(source="record_values", many=True, read_only=True)
    status = serializers.SerializerMethodField()

    class Meta:
        model = Records
        fields = 'indicator_value', 'status'

    def get_status(self, obj):
        last_status = obj.history.last()
        if last_status:
            return last_status.status_list.short_name
        return None
