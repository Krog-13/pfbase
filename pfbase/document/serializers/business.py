import datetime
from pfbase.dictionary.models import *
from pfbase.document.models.business import *
from pfbase.document.models.documents import Documents
from pfbase.system.models.listvalues import ListValues
from pfbase.system.models.organization import Organization
from pfbase.system.models.user import User
from pfbase.dictionary.serializers.business import *


def validate_reference_field(value, model_cls, field_label):
    if not model_cls.objects.filter(pk=value).exists():
        raise serializers.ValidationError(f"{field_label} с ID {value} не найден(а).")
    return value


def BusinessDocumentModelSerializer(document_code):
    try:
        document = Documents.objects.get(code=document_code)
    except ObjectDoesNotExist:
        raise ValueError(f"Документ с кодом '{document_code}' не найден")

    dynamic_model = BusinessDocumentModel(document_code)

    class BusinessDocumentModelRecordSerializer(serializers.ModelSerializer):
        list_values = ListValues.objects.all()
        organization_values = Organization.objects.all()

        # Это место нужно переделать. На текущий момент загружаются все пользователи.
        # Сделано было чтоб уменьшить обращения в базу. Теперь внизу в цикле они вытягиваются как справочники
        user_values = User.objects.all()

        indicators_dict = document.indicators.filter(type_value=IndicatorType.DICTIONARY)

        grouped_list_values = {}
        grouped_organization_values = {}
        grouped_user_values = {}

        for element in list_values:
            grouped_list_values.setdefault(element.id, []).append(element)

        for element in organization_values:
            grouped_organization_values.setdefault(element.id, []).append(element)

        for element in user_values:
            grouped_user_values.setdefault(element.id, []).append(element)

        class Meta:
            model = dynamic_model
            fields = '__all__'

        def get_filtered_data(self, *field_names):
            """
            Возвращает данные сериализатора, содержащие только указанные поля.
            Если self.data – это словарь, возвращает словарь, если список – список словарей.
            """
            data = self.data
            if isinstance(data, dict):
                return {field: data.get(field) for field in field_names}
            elif isinstance(data, list):
                return [{field: item.get(field) for field in field_names} for item in data]
            return data


        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            base_fields = {'id', 'number', 'date', 'active', 'organization', 'parent'}
            self.fields["author"].required = False
            for field_name, field in self.fields.items():
                if field_name not in base_fields:
                    field.required = False

        def validate(self, data):
            errors = {}

            for indicator in document.indicators.filter(
                type_value__in=[IndicatorType.LIST, IndicatorType.USER, IndicatorType.ORGANIZATION, IndicatorType.DOCUMENT]
            ):
                field_key = indicator.code
                if field_key in data:
                    ref_id = data[field_key]
                    if indicator.type_value == IndicatorType.LIST:
                        try:
                            validate_reference_field(ref_id, ListValues, "ListValues")
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
                            validate_reference_field(ref_id, Documents, "Документ")
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

        def to_representation(self, instance):
            rep = super().to_representation(instance)

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

            element_ids = [rep.get(ind.code) for ind in self.indicators_dict if rep.get(ind.code) is not None]

            elements = Elements.objects.filter(pk__in=element_ids)
            elements_map = {str(el.pk): el for el in elements}

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

            other_types = [IndicatorType.LIST, IndicatorType.USER, IndicatorType.ORGANIZATION, IndicatorType.DOCUMENT]

            for indicator in document.indicators.filter(type_value__in=other_types):
                field_key = indicator.code
                ref_id = rep.get(field_key)
                if ref_id:
                    try:
                        if indicator.type_value == IndicatorType.LIST:
                            objs = self.grouped_list_values.get(ref_id, [])
                            if objs:
                                obj = objs[0]
                                rep[field_key] = {'id': obj.id, 'code': obj.code, 'short_name': obj.short_name, 'full_name': obj.full_name}
                        elif indicator.type_value == IndicatorType.USER:
                            objs = self.grouped_user_values.get(ref_id, [])
                            if objs:
                                obj = objs[0]
                                rep[field_key] = {'id': obj.id, 'username': obj.username, 'email': obj.email}
                        elif indicator.type_value == IndicatorType.ORGANIZATION:
                            objs = self.grouped_organization_values.get(ref_id, [])
                            if objs:
                                obj = objs[0]
                                rep[field_key] = {'id': obj.id, 'short_name': obj.short_name, 'full_name': obj.full_name}
                        elif indicator.type_value == IndicatorType.DOCUMENT:
                            obj = Documents.objects.get(pk=ref_id)
                            rep[field_key] = {'id': obj.id, 'name': obj.name, 'code': obj.code}
                    except ObjectDoesNotExist:
                        rep[field_key] = {"error": f"Объект для {indicator.get_type_value_display()} с ID {ref_id} не найден."}
            return rep

    return BusinessDocumentModelRecordSerializer


