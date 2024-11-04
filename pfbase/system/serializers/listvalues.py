from rest_framework import serializers
from ..models.listvalues import ListValues


class LValuesSerializer(serializers.ModelSerializer):
    short_name = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = ListValues
        fields = "__all__"

    def get_short_name(self, obj):
        query_params = self.context['request'].query_params
        lang = query_params.get('lang', 'ru')
        return obj.short_name.get(lang)

    def get_full_name(self, obj):
        query_params = self.context['request'].query_params
        lang = query_params.get('lang', 'ru')
        return obj.full_name.get(lang)
