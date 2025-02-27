from rest_framework import serializers
from pfbase.dictionary.models.business import BusinessDictionaryModel

_dynamic_serializer_cache = {}


def BusinessDictionarySerializer(dictionary_code):
    if dictionary_code in _dynamic_serializer_cache:
        return _dynamic_serializer_cache[dictionary_code]

    dynamic_model = BusinessDictionaryModel(dictionary_code)

    class BusinessDictionaryElementSerializer(serializers.ModelSerializer):
        class Meta:
            model = dynamic_model
            fields = '__all__'

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            base_fields = {'id', 'short_name', 'full_name', 'code', 'active'}
            for field_name, field in self.fields.items():
                if field_name not in base_fields:
                    field.required = False

        def create(self, validated_data):
            return dynamic_model.objects.create(**validated_data)

        def update(self, instance, validated_data):
            for field in validated_data:
                setattr(instance, field, validated_data[field])
            instance.save()
            return instance

    _dynamic_serializer_cache[dictionary_code] = BusinessDictionaryElementSerializer
    return BusinessDictionaryElementSerializer
