"""
Serializers for the models in the pfbase app
"""
from rest_framework import serializers
from ..models.dictionaries import Dictionaries


# serializers for Dictionary
class DictionarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Dictionaries
        fields = "__all__"
