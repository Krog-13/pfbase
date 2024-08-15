from .models import AutoCatalog
from rest_framework import serializers


def detect_entity(instance):
    """
    Detect instance model
    """
    if instance.description == "AutoCatalog":
        auto_data = AutoCatalog.objects.all()
        serialized_auto_data = AutoCatalogSerializer(auto_data, many=True).data
        return serialized_auto_data
    elif instance.description == "Drive":
        pass


class AutoCatalogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AutoCatalog
        fields = ("id", "short_name", "model_car")