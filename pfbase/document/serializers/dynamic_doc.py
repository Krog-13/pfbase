import datetime
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers
from pfbase.document.models.dynamic_doc import *
from pfbase.dictionary.models import *
from pfbase.dictionary.serializers.dynamic_dict import *


def DynamicSerializer(document_code):
    try:
        document = Documents.objects.get(code=document_code)
    except ObjectDoesNotExist:
        raise ValueError(f"Документ с кодом '{document_code}' не найден")

    dynamic_model = DynamicModel(document_code)

    class DynamicRecordSerializer(serializers.ModelSerializer):
        class Meta:
            model = dynamic_model
            fields = '__all__'

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            base_fields = {'id', 'number', 'date', 'active'}
            for field_name, field in self.fields.items():
                if field_name not in base_fields:
                    field.required = False

        def create(self, validated_data):
            return dynamic_model.objects.create(date=datetime.datetime.now(), **validated_data)

        def update(self, instance, validated_data):
            return dynamic_model.objects.update_instance(instance, **validated_data)

        def to_representation(self, instance):
            rep = super().to_representation(instance)
            indicators = document.indicators.filter(type_value=IndicatorType.DICTIONARY)

            element_ids = [
                rep.get(indicator.code)
                for indicator in indicators
                if rep.get(indicator.code) is not None
            ]

            elements = Elements.objects.filter(pk__in=element_ids)
            elements_map = {str(element.pk): element for element in elements}

            for indicator in indicators:
                field_key = indicator.code
                element_id = rep.get(field_key)
                if element_id:
                    dictionary_code = indicator.type_extend
                    try:
                        DictSerializerClass = DynamicDictionarySerializer(dictionary_code)
                        element = elements_map.get(str(element_id))
                        if element:
                            rep[field_key] = DictSerializerClass(element).data
                        else:
                            rep[field_key] = {"error": f"Element with pk {element_id} not found."}
                    except Exception as e:
                        rep[field_key] = {"error": str(e)}

            return rep

    return DynamicRecordSerializer
