"""
Serializers for the models in the pfbase app
"""
from rest_framework import serializers
from ..models.documents import Documents


class DocumentSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()

    class Meta:
        model = Documents
        fields = "__all__"

    def get_name(self, obj):
        query_params = self.context['request'].query_params
        lang = query_params.get('lang', 'ru')
        return obj.name.get(lang)

    def get_description(self, obj):
        query_params = self.context['request'].query_params
        lang = query_params.get('lang', 'ru')
        return obj.description.get(lang)
