from pfbase.system.models.listvalues import ListValues
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
    short_name = serializers.JSONField(source='indicator.short_name')
    type_value = serializers.CharField(source='indicator.type_value')
    type_extend = serializers.CharField(source='indicator.type_extend')
    code = serializers.CharField(source='indicator.code')
    value = serializers.SerializerMethodField()

    class Meta:
        model = ElementIndicatorValues
        fields = 'id', 'short_name', 'code', 'type_value', 'type_extend', 'value_reference', 'value'

    def get_value_name(self, obj):
        if obj.indicator.type_value == 'dct':
            element = Elements.objects.get(id=obj.value_reference)
            return element.short_name
        elif obj.indicator.type_value == 'list':
            record = ListValues.objects.get(id=obj.value_reference)
            return record.short_name

    def get_value(self, obj):
        value_fields = [
            'value_int', 'value_text', 'value_datetime',
            'value_bool', 'value_str', 'value_json', 'value_float']
        for field in value_fields:
            if obj.indicator.type_value in ['dct', 'list']:
                return self.get_value_name(obj)
            if value := getattr(obj, field, None):
                return value
        return None


class EIGetSerializer(serializers.ModelSerializer):
    short_name = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()
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

    def get_short_name(self, obj):
        query_params = self.context['request'].query_params
        lang = query_params.get('lang')
        if not lang or lang not in ["ru", "en", "kk"]:
            return obj.short_name
        short_name = obj.short_name.get(lang, None)
        obj.short_name = {}
        obj.short_name[lang] = short_name
        return obj.short_name

    def get_full_name(self, obj):
        query_params = self.context['request'].query_params
        lang = query_params.get('lang')
        if not lang or lang not in ["ru", "en", "kk"] or not obj.full_name:
            return obj.full_name
        full_name = obj.full_name.get(lang, None)
        obj.full_name = {}
        obj.full_name[lang] = full_name
        return obj.full_name


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
    id = serializers.IntegerField(required=False)
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
    organization_id = serializers.IntegerField(required=False)

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
    dictionary_id = serializers.IntegerField(required=False)
    organization_id = serializers.IntegerField(required=False)

    def update(self, instance, validated_data):
        user = self.context['request'].user
        try:
            return ElementService().update_element_iv(instance, user, validated_data)
        except ValidationError as e:
            raise exceptions.ValidationError({"error": str(e)})
