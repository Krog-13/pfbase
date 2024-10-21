"""
Serializers for the models in the pfbase app
"""
from rest_framework import serializers
from ..models.documents import Documents


class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Documents
        fields = "__all__"
