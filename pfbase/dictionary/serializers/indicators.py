from rest_framework import serializers
from ..models.indicators import DctIndicators


class IndicatorSerializer(serializers.ModelSerializer):
    short_name = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()

    class Meta:
        model = DctIndicators
        fields = "__all__"

    def get_short_name(self, obj):
        query_params = self.context['request'].query_params
        lang = query_params.get('lang', 'ru')
        return obj.short_name.get(lang)

    def get_full_name(self, obj):
        query_params = self.context['request'].query_params
        lang = query_params.get('lang', 'ru')
        return obj.full_name.get(lang)

    def get_description(self, obj):
        query_params = self.context['request'].query_params
        lang = query_params.get('lang', 'ru')
        return obj.description.get(lang)
