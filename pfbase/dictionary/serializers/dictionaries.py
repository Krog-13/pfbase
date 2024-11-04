"""
Serializers for the models in the pfbase app
"""
from rest_framework import serializers
from ..models.dictionaries import Dictionaries


# serializers for Dictionary
class DictionarySerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()

    class Meta:
        model = Dictionaries
        fields = "__all__"

    def get_name(self, obj):
        query_params = self.context['request'].query_params
        lang = query_params.get('lang')
        if not lang or lang not in ["ru", "en", "kk"]:
            return obj.name
        name = obj.name.get(lang, None)
        obj.name = {}
        obj.name[lang] = name
        return obj.name

    def get_description(self, obj):
        query_params = self.context['request'].query_params
        lang = query_params.get('lang')
        if not lang or lang not in ["ru", "en", "kk"]:
            return obj.description
        description = obj.description.get(lang, None)
        obj.description = {}
        obj.description[lang] = description
        return obj.description
