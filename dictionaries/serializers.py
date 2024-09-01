from rest_framework import serializers, fields
from .models import Category, IndicatorParameter, Indicator, ElementIndicatorValue, \
    ABCDictionary, Element


class IndicatorValueSerializer(serializers.ModelSerializer):
    """
    Serializer for indicator values
    """
    indicator_meta = serializers.SerializerMethodField()

    class Meta:
        model = ElementIndicatorValue
        fields = ("indicator_value", "indicator_meta")

    def get_indicator_meta(self, obj):
        if obj.indicator:
            indicator = obj.indicator
            return {"short_name": indicator.short_name, "type_value": indicator.type_value}


class ElementSerializer(serializers.ModelSerializer):
    """
    Serializer for elements
    """
    children = serializers.SerializerMethodField()
    indicator = IndicatorValueSerializer(many=True, read_only=True)
    # indicator = serializers.StringRelatedField(many=True) # покажет FK значения

    class Meta:
        model = Element
        fields = ("id", "short_name", "parent", "children", "abc_dictionary", "indicator")

    def get_children(self, obj):
        """
        Check for child categories
        """
        children_qs = obj.children.all()
        if children_qs.exists():
            return True
        return False


class ElementSerializerSoft(serializers.ModelSerializer):
    """
    Serializer for elements by soft
    """
    children = serializers.SerializerMethodField()

    class Meta:
        model = Element
        fields = ("id", "short_name", "parent", "children", "abc_dictionary")

    def get_children(self, obj):
        """
        Check for child categories
        """
        children_qs = obj.children.all()
        if children_qs.exists():
            return True
        return False


class CategoryDictionarySerializer(serializers.ModelSerializer):
    """
    Сериализатор для категорий справочников
    """
    children = serializers.SerializerMethodField()
    dictionaries = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ("id", "short_name", "description",
                  "index_sort", "parent", "children", "dictionaries")

    def get_children(self, obj):
        """
        Функция для проверки дочерних категорий
        """
        children_qs = obj.children.all()
        if children_qs.exists():
            return True
        return False

    def get_dictionaries(self, obj):
        """
        Функция для проверки справочников в категории
        """
        dictionaries = ABCDictionary.objects.filter(category_dictionary=obj.id)
        if dictionaries.exists():
            return True
        return False


class DictionarySerializer(serializers.ModelSerializer):
    """
    Сериализатор для справочников
    """
    class Meta:
        model = ABCDictionary
        fields = ("id", "naming", "description", "organizations", "category_dictionary")





class IndicatorSerializer(serializers.ModelSerializer):
    """
    Сериализатор для показателей
    """
    # parameters = serializers.SlugRelatedField(
    #     slug_field="short_name", queryset=DefaultParameter.objects.all(), many=True)

    class Meta:
        model = Indicator
        fields = ("id", "short_name", "type_value", "parameters", "dictionary")



