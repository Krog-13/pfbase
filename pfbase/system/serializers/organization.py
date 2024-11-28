from rest_framework import serializers
from ..models.organization import Organization


class OrganizationSerializer(serializers.ModelSerializer):
    short_name = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = Organization
        fields = "__all__"

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

class OrganizationCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Organization
        fields = "__all__"
