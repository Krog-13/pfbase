from rest_framework import serializers, exceptions
from rest_framework.exceptions import ValidationError
from ..models.eivalues import ElementIndicatorValues
from ..models.elements import Elements
from ..service import ElementService


class ElementSerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()

    class Meta:
        model = Elements
        fields = "__all__"

    def get_children(self, obj):
        children_qs = obj.children.all()
        if children_qs.exists():
            return True
        return False


class EIValueSerializer(serializers.ModelSerializer):
    name = serializers.JSONField(source='indicator.name')
    type_value = serializers.CharField(source='indicator.type_value')
    type_extend = serializers.CharField(source='indicator.type_extend')
    value = serializers.SerializerMethodField()

    class Meta:
        model = ElementIndicatorValues
        fields = 'id', 'name', 'type_value', 'type_extend', 'value_reference', 'value'

    def get_value_name(self, obj):
        if obj.indicator.type_value == 'dct':
            element = Elements.objects.get(id=obj.value_reference)
            return element.short_name

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


class EIGetSerializer(serializers.ModelSerializer):
    indicator_value = EIValueSerializer(source="element_values", many=True, read_only=True)
    children = serializers.SerializerMethodField()

    class Meta:
        model = Elements
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


class EIPostSerializer(CommonSerializer):
    short_name = serializers.JSONField()
    full_name = serializers.JSONField(required=False)
    dictionary_id = serializers.IntegerField()
    code = serializers.CharField(max_length=50, required=False)
    parent_id = serializers.IntegerField(required=False)
    indicators = IndicatorSerializer(many=True, required=False)

    def create(self, validated_data):

        user = self.context['request'].user
        if not user:
            user = self.context['user']
        try:
            return ElementService().create_element_iv(user, validated_data)
        except ValidationError as e:
            raise exceptions.ValidationError({"error": str(e)})


class EIUpdateSerializer(CommonSerializer):
    short_name = serializers.JSONField(required=False)
    full_name = serializers.JSONField(required=False)
    code = serializers.CharField(max_length=50, required=False)
    parent_id = serializers.IntegerField(required=False)
    indicators = IndicatorSerializer(many=True, required=False)

    def update(self, instance, validated_data):
        user = self.context['request'].user
        try:
            return ElementService().update_record_iv(instance, user, validated_data)
        except ValidationError as e:
            raise exceptions.ValidationError({"error": str(e)})
