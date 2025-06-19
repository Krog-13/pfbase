from rest_framework import serializers, exceptions
from rest_framework.exceptions import ValidationError
from ..models.records import Records
from ..models.rivalues import RecordIndicatorValues
from pfbase.dictionary.models.elements import Elements
from pfbase.system.models.listvalues import ListValues
from pfbase.system.models.user import User
from ..service import RecordService
import datetime

from ...system.models import Organization


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
    # shortname = serializers.JSONField(source='indicator.short_name')
    short_name = serializers.SerializerMethodField(source='indicator.short_name')
    full_name = serializers.SerializerMethodField(source='indicator.full_name')
    type_value = serializers.CharField(source='indicator.type_value')
    type_extend = serializers.CharField(source='indicator.type_extend')
    is_multiple = serializers.CharField(source='indicator.is_multiple')
    code = serializers.CharField(source='indicator.code')
    value = serializers.SerializerMethodField()

    class Meta:
        model = RecordIndicatorValues
        fields = 'id', 'short_name', 'full_name', 'code', 'type_value', 'type_extend', 'is_multiple', 'value_reference', 'value'


    def get_short_name(self, obj):
        query_params = self.context['request'].query_params
        lang = query_params.get('lang')
        if not lang or lang not in ["ru", "en", "kk"]:
            return obj.indicator.short_name
        short_name = obj.indicator.short_name.get(lang, None)
        obj.indicator.short_name = {}
        obj.indicator.short_name[lang] = short_name
        return obj.indicator.short_name

    def get_full_name(self, obj):
        query_params = self.context['request'].query_params
        lang = query_params.get('lang')
        if not lang or lang not in ["ru", "en", "kk"]:
            return obj.indicator.full_name
        full_name = obj.indicator.full_name.get(lang, None)
        obj.indicator.full_name = {}
        obj.indicator.full_name[lang] = full_name
        return obj.indicator.full_name

    def get_value_name(self, obj):
        query_params = self.context['request'].query_params
        lang = query_params.get('lang', 'ru')
        if obj.indicator.type_value == 'dct':
            if obj.indicator.is_multiple:
                return obj.value_array_int
            element = Elements.objects.filter(id=obj.value_reference).first()
            return element.short_name.get(lang) if element else None
        elif obj.indicator.type_value == 'list':
            if obj.indicator.is_multiple:
                return obj.value_array_int
            record = ListValues.objects.filter(id=obj.value_reference).first()
            return record.short_name.get(lang) if record else None
        elif obj.indicator.type_value == 'dcm':
            if obj.indicator.is_multiple:
                return obj.value_array_int
            rec = Records.objects.filter(id=obj.value_reference).first()
            return rec.number
        elif obj.indicator.type_value == 'user':
            usr = User.objects.filter(id=obj.value_reference).first()
            return f"{usr.first_name} {usr.last_name}"
        elif obj.indicator.type_value == 'org':
            org = Organization.objects.filter(id=obj.value_reference).first()
            return org.short_name.get(lang)
        
    def get_value(self, obj):
        type_value = obj.indicator.type_value
        is_multiple = obj.indicator.is_multiple
        if type_value in ["dct", "list", "dcm", "user", "org"]:
            return self.get_value_name(obj)
        mapping = {"str": "value_str", "text": "value_text", "date": "value_datetime", "int": "value_int", "float": "value_float",
                   "datetime": "value_datetime", "file": "value_str", "bool": "value_bool", "time": "value_datetime", "json": "value_json"}
        mapping_multiple = {"str": "value_array_str", "text": "value_array_str",
                            "int": "value_array_int", "file": "value_array_str", "date": "value_array_str"}
        if is_multiple:
            value = getattr(obj, mapping_multiple[type_value], None)
        else:
            value = getattr(obj, mapping[type_value], None)
        return value


class RecordsSerializer(serializers.ModelSerializer):
    indicator_value = RIValueSerializer(source="record_values", many=True, read_only=True)
    children = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()

    class Meta:
        model = Records
        fields = "__all__"

    def get_children(self, obj):
        children_qs = obj.children.all()
        if children_qs.exists():
            return True
        return False

    def get_status(self, obj):
        last_status = obj.history.last()
        if last_status:
            return last_status.status.short_name
        return None


class RIGetSerializer(serializers.ModelSerializer):
    code = serializers.CharField(source="document.code", required=False)
    indicator_value = RIValueSerializer(source="record_values", many=True, read_only=True)
    status = serializers.SerializerMethodField()
    children = serializers.SerializerMethodField()
    organization_detail = serializers.SerializerMethodField()

    class Meta:
        model = Records
        fields = '__all__'

    def get_status(self, obj):
        last_status = obj.history.last()
        if last_status:
            return last_status.status.short_name
        return None

    def get_children(self, obj):
        children_qs = obj.children.all()
        if children_qs.exists():
            return True
        return False

    def get_organization_detail(self, obj):
        org_id = obj.organization.id if obj.organization else None
        short_name = obj.organization.short_name if obj.organization else None
        return {"id": org_id,
                "short_name": short_name}


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


class CustomField(serializers.Field):
    def to_representation(self, value):
        # Output the value as it is
        return value

    def to_internal_value(self, data):
        # Allow only strings, integers, and booleans
        if isinstance(data, (str, int, bool, list, dict)):
            return data
        raise serializers.ValidationError("Value must be an integer, string, or boolean.")


class IndicatorSerializer(CommonSerializer):
    id = serializers.IntegerField(required=False)
    value = CustomField(required=True, allow_null=True)
    code = serializers.CharField(max_length=50, required=False)
    type = serializers.CharField(max_length=10, required=False)

class IndicatorAnySerializer(CommonSerializer):
    id = serializers.IntegerField(required=False)
    code = serializers.CharField(max_length=50, required=False)
    value_str = serializers.CharField(required=False, allow_null=True)
    value_int = serializers.IntegerField(required=False, allow_null=True)
    value_reference = serializers.IntegerField(required=False, allow_null=True)
    value_float = serializers.FloatField(required=False, allow_null=True)
    value_text = serializers.CharField(required=False, allow_null=True)
    value_json = serializers.JSONField(required=False, allow_null=True)
    value_datetime = serializers.DateTimeField(required=False, allow_null=True)
    value_bool = serializers.BooleanField(required=False, allow_null=True)
    value_list = serializers.IntegerField(required=False, allow_null=True)
    type = serializers.CharField(max_length=10, required=False)

class IndicatorUpdateSerializer(CommonSerializer):
    id = serializers.IntegerField(required=True)
    value = CustomField(required=True, allow_null=True)
    type = serializers.CharField(max_length=100, required=True)

class RecordFormDataSerializer(serializers.Serializer):
    file = serializers.FileField(required=True)
    data = serializers.JSONField(required=True)

    def create(self, validated_data):
        user = self.context['request'].user
        if not user:
            user = self.context['user']
        try:
            pass
        except ValidationError as e:
            raise exceptions.ValidationError({"error": str(e)})

class RecordPostSerializer(CommonSerializer):
    number = serializers.CharField(required=False, default="0000")
    date = serializers.DateTimeField(required=False, default=datetime.datetime.now())
    document_id = serializers.IntegerField(required=False)
    code = serializers.CharField(required=False)
    parent_id = serializers.IntegerField(required=False)
    indicators = IndicatorSerializer(many=True, required=False)
    status_id = serializers.IntegerField(required=False)
    organization_id = serializers.IntegerField(required=False)

    def create(self, validated_data):
        user = self.context['request'].user
        if not user:
            user = self.context['user']
        try:
            return RecordService().create_record_iv(user, validated_data)
        except ValidationError as e:
            raise exceptions.ValidationError({"error": str(e)})

class RecordListPostSerializer(serializers.Serializer):
    records = serializers.ListField(required=True)

    def create(self, validated_data):
        user = self.context['request'].user
        if not user:
            user = self.context['user']
        try:
            return RecordService().create_record_list(user, validated_data)
        except ValidationError as e:
            raise exceptions.ValidationError({"error": str(e)})



class RecordAnyPostSerializer(CommonSerializer):
    number = serializers.CharField(required=False, default="0000")
    date = serializers.DateTimeField(required=False, default=datetime.datetime.now())
    document_id = serializers.IntegerField(required=False)
    code = serializers.CharField(required=False)
    parent_id = serializers.IntegerField(required=False)
    indicators = IndicatorAnySerializer(many=True, required=False)
    status_id = serializers.IntegerField(required=False)
    organization_id = serializers.IntegerField(required=False)

    def create(self, validated_data):
        user = self.context['request'].user
        if not user:
            user = self.context['user']
        try:
            return RecordService().create_record_any_iv(user, validated_data)
        except ValidationError as e:
            raise exceptions.ValidationError({"error": str(e)})


class RecordPackPostSerializer(serializers.Serializer):
    main = serializers.JSONField(required=True)
    subs = serializers.ListField(required=True)

    def create(self, request_data):
        user = self.context['request'].user
        if not user:
            user = self.context['user']
        try:
            return RecordService().create_record_pack(user, request_data)
        except ValidationError as e:
            raise exceptions.ValidationError({"error": str(e)})
        except KeyError as e:
            raise exceptions.ValidationError({"error": str(e)})
        except Exception as e:
            raise exceptions.ValidationError({"error": str(e)})


class RecordUpdateSerializer(CommonSerializer):
    number = serializers.CharField(required=False)
    date = serializers.DateField(required=False)
    parent_id = serializers.IntegerField(required=False)
    record_id = serializers.IntegerField(required=True)
    status_id = serializers.IntegerField(required=False)
    organization_id = serializers.IntegerField(required=False)
    indicators = IndicatorUpdateSerializer(many=True, required=False)

    def update(self, instance, validated_data):
        user = self.context['request'].user
        try:
            return RecordService().update_record_iv(instance, user, validated_data)
        except ValidationError as e:
            raise exceptions.ValidationError({"error": str(e)})


class RecordPackUpdateSerializer(serializers.Serializer):
    main = serializers.JSONField(required=True)
    subs = serializers.ListField(required=True)

    def update(self, instance, request_data):
        user = self.context['request'].user
        try:
            return RecordService().update_record_pack(user, request_data)
        except ValidationError as e:
            raise exceptions.ValidationError({"error": str(e)})
        except Exception as e:
            raise exceptions.ValidationError({"error": str(e)})


class RecordListUpdateSerializer(serializers.Serializer):
    records = serializers.ListField(required=True)

    def update(self, instance, validated_data):
        user = self.context['request'].user
        try:
            return RecordService().update_records_list(user, validated_data)
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
