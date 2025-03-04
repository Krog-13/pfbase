import datetime
from pfbase.dictionary.models import *
from pfbase.document.models.business import *
from pfbase.document.models.documents import Documents
from pfbase.system.models.listvalues import ListValues
from pfbase.system.models.organization import Organization
from pfbase.system.models.user import User
from pfbase.system.serializers.common import FileSaveSerializer
from pfbase.dictionary.serializers.business import *
from django.core.files.uploadedfile import InMemoryUploadedFile, TemporaryUploadedFile


def validate_reference_field(value, model_cls, field_label):
    if not model_cls.objects.filter(pk=value).exists():
        raise serializers.ValidationError(f"{field_label} с ID {value} не найден(а).")
    return value


def validate_dictionary_field(value, type_extend):
    if not Dictionaries.objects.filter(code=type_extend).exists():
        raise serializers.ValidationError(f"Справочник в индикаторе с ID {type_extend} не найден(а).")

    if not Elements.objects.filter(dictionary__code=type_extend, pk=value).exists():
        raise serializers.ValidationError(f"Справочник с ID {value} не найден(а).")
    return value


def validate_document_field(value, type_extend):
    if not Documents.objects.filter(code=type_extend).exists():
        raise serializers.ValidationError(f"Документ в индикаторе с кодом {type_extend} не найден(а).")

    if not Records.objects.filter(document__code=type_extend, pk=value).exists():
        raise serializers.ValidationError(f"Запись в документ {type_extend} с ID {value} не найден(а).")
    return value


def validate_list_field(value, type_extend):
    if not ListValues.objects.filter(list=type_extend).exists():
        raise serializers.ValidationError(f"ListValue в индикаторе с кодом {type_extend} не найден(а).")

    if not ListValues.objects.filter(list=type_extend, pk=value).exists():
        raise serializers.ValidationError(f"Запись в ListValue {type_extend} с ID {value} не найден(а).")
    return value


class CustomListSerializer(serializers.ListSerializer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.initial_queryset = self.instance

    def get_details(self, value=True):
        self.child.is_detail_show = value
        return self

    def only_fields(self, *fields):
        self.child._only_fields = set(fields)
        return self


class FileUploadField(serializers.FileField):
    def to_representation(self, value):
        if isinstance(value, str):
            return value
        return super().to_representation(value)


def BusinessDocumentModelSerializer(document_code):
    try:
        document = Documents.objects.get(code=document_code)
    except ObjectDoesNotExist:
        raise ValueError(f"Документ с кодом '{document_code}' не найден")

    dynamic_model = BusinessDocumentModel(document_code)

    class BusinessDocumentModelRecordSerializer(serializers.ModelSerializer):
        is_detail_show = False
        dct_loaded = False
        dictionary_values = None

        organization_values = Organization.objects.all()
        document_values = Documents.objects.all()
        list_values = ListValues.objects.all()
        user_values = User.objects.all()

        other_types = [
            IndicatorType.LIST,
            IndicatorType.USER,
            IndicatorType.ORGANIZATION,
            IndicatorType.DOCUMENT,
        ]
        precomputed_other_indicators = list(document.indicators.filter(type_value__in=other_types))

        indicators_dict = document.indicators.filter(type_value=IndicatorType.DICTIONARY)
        other_indicators = precomputed_other_indicators

        other_ind = document.indicators.filter(type_value__in=other_types)
        grouped_list_values = {}
        grouped_organization_values = {}
        grouped_user_values = {}
        grouped_document_values = {}

        queryset_result = []

        class Meta:
            model = dynamic_model
            fields = '__all__'
            list_serializer_class = CustomListSerializer

        for element in organization_values:
            grouped_organization_values.setdefault(element.id, []).append(element)

        for element in user_values:
            grouped_user_values.setdefault(element.id, []).append(element)

        for element in document_values:
            grouped_document_values.setdefault(element.id, []).append(element)

        for element in list_values:
            grouped_list_values.setdefault(element.id, []).append(element)

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.initial_queryset = self.instance
            base_fields = {'id', 'number', 'date', 'active', 'organization', 'parent'}
            self.fields["author"].required = False

            for field_name, field in self.fields.items():
                if field_name not in base_fields:
                    field.required = False

            for indicator in document.indicators.all():
                if getattr(indicator, 'is_required', False):
                    if indicator.code in self.fields:
                        self.fields[indicator.code].required = True

            for indicator in document.indicators.filter(type_value=IndicatorType.FILE):
                if indicator.code in self.fields:
                    self.fields[indicator.code] = FileUploadField(required=getattr(indicator, 'is_required', False))

        def validate(self, data):
            errors = {}
            for indicator in document.indicators.filter(
                    type_value__in=[
                        IndicatorType.LIST,
                        IndicatorType.USER,
                        IndicatorType.ORGANIZATION,
                        IndicatorType.DOCUMENT,
                        IndicatorType.DICTIONARY,
                        IndicatorType.FILE
                    ]
            ):
                field_key = indicator.code
                if field_key in data:
                    ref_id = data[field_key]
                    if indicator.type_value == IndicatorType.FILE:
                        try:
                            if not ref_id:
                                raise serializers.ValidationError(f"Файл для {field_key} не передан.")
                            if not isinstance(ref_id, (InMemoryUploadedFile, TemporaryUploadedFile)):
                                raise serializers.ValidationError(f"Значение для {field_key} должно быть файлом.")

                            file_serializer = FileSaveSerializer(data={'file': ref_id})
                            file_serializer.is_valid(raise_exception=True)
                            file_data_saved = file_serializer.save()
                            data[field_key] = file_data_saved
                        except serializers.ValidationError as e:
                            errors[field_key] = e.detail
                        except Exception as e:
                            errors[field_key] = str(e)

                    elif indicator.type_value == IndicatorType.LIST:
                        try:
                            validate_list_field(ref_id, indicator.type_extend)
                        except serializers.ValidationError as e:
                            errors[field_key] = e.detail
                    elif indicator.type_value == IndicatorType.USER:
                        try:
                            validate_reference_field(ref_id, User, "Пользователь")
                        except serializers.ValidationError as e:
                            errors[field_key] = e.detail
                    elif indicator.type_value == IndicatorType.ORGANIZATION:
                        try:
                            validate_reference_field(ref_id, Organization, "Организация")
                        except serializers.ValidationError as e:
                            errors[field_key] = e.detail
                    elif indicator.type_value == IndicatorType.DOCUMENT:
                        try:
                            validate_document_field(ref_id, indicator.type_extend)
                        except serializers.ValidationError as e:
                            errors[field_key] = e.detail
                    elif indicator.type_value == IndicatorType.DICTIONARY:
                        try:
                            validate_dictionary_field(ref_id, indicator.type_extend)
                        except serializers.ValidationError as e:
                            errors[field_key] = e.detail

            if errors:
                raise serializers.ValidationError(errors)
            return data

        def create(self, validated_data):
            if not validated_data.get('author'):
                validated_data['author'] = self.context.get("request").user
            if not validated_data.get('date'):
                validated_data['date'] = datetime.datetime.now()
            return dynamic_model.objects.create(**validated_data)

        def update(self, instance, validated_data):
            return dynamic_model.objects.update_instance(instance, **validated_data)

        def only_fields(self, *fields):
            self._only_fields = set(fields)
            return self

        def unset_required(self):
            for indicator in document.indicators.all():
                if getattr(indicator, 'is_required', False) and indicator.code in self.fields:
                    self.fields[indicator.code].required = False
            return self

        def queryset(self):
            return self.initial_queryset

        def queryset_bind(self):
            if len(self.queryset_result) == 0:
                self.queryset_result = self.queryset()

        def load_dictionary_values(self):
            if not self.dct_loaded:
                queryset = self.initial_queryset
                objects_list = queryset
                self.dct_loaded = True
                dct_ids_global = []
                for obj in objects_list:
                    for ind_dct in self.indicators_dict:
                        dct_ids_global.append(getattr(obj, ind_dct.code))
                self.dictionary_values = Elements.objects.filter(pk__in=dct_ids_global)

        def to_representation(self, instance):
            self.queryset_bind()

            rep = super().to_representation(instance)

            if not self.is_detail_show:
                return rep

            self.load_dictionary_values()

            if instance.author:
                rep['author'] = {'id': instance.author.id, 'username': instance.author.username}
            else:
                rep['author'] = None
            if instance.organization:
                rep['organization'] = {'id': instance.organization.id, 'name': instance.organization.short_name}
            else:
                rep['organization'] = None
            if instance.parent:
                rep['parent'] = {'id': instance.parent.id, 'number': instance.parent.number, 'date': instance.parent.date}
            else:
                rep['parent'] = None

            elements_map = {str(el.pk): el for el in self.dictionary_values}

            for indicator in self.indicators_dict:
                field_key = indicator.code
                element_id = rep.get(field_key)
                if element_id:
                    dictionary_code = indicator.type_extend
                    try:
                        DictSerializerClass = BusinessDictionarySerializer(dictionary_code)
                        element = elements_map.get(str(element_id))
                        if element:
                            rep[field_key] = DictSerializerClass(element).data
                        else:
                            rep[field_key] = {"error": f"Элемент справочника с pk {element_id} не найден."}
                    except Exception as e:
                        rep[field_key] = {"error": str(e)}

            for indicator in self.other_indicators:
                field_key = indicator.code

                ref_id = rep.get(field_key)

                if ref_id:
                    try:
                        if indicator.type_value == IndicatorType.LIST:
                            objs = self.grouped_list_values.get(ref_id, [])
                            if objs:
                                obj = objs[0]
                                rep[field_key] = {'id': obj.id, 'code': obj.code, 'short_name': obj.short_name,
                                                  'full_name': obj.full_name}
                        elif indicator.type_value == IndicatorType.USER:
                            objs = self.grouped_user_values.get(ref_id, [])
                            if objs:
                                obj = objs[0]
                                rep[field_key] = {'id': obj.id, 'username': obj.username, 'email': obj.email}
                        elif indicator.type_value == IndicatorType.ORGANIZATION:
                            objs = self.grouped_organization_values.get(ref_id, [])
                            if objs:
                                obj = objs[0]
                                rep[field_key] = {'id': obj.id, 'short_name': obj.short_name,
                                                  'full_name': obj.full_name}
                    except ObjectDoesNotExist:
                        rep[field_key] = {
                            "error": f"Объект для {indicator.get_type_value_display()} с ID {ref_id} не найден."}

            if hasattr(self, '_only_fields'):
                rep = {k: v for k, v in rep.items() if k in self._only_fields}

            return rep

    return BusinessDocumentModelRecordSerializer


