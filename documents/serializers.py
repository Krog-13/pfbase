from rest_framework import serializers
from .models import CategoryDocument,  IndicatorParameter, FieldValue, ABCDocument, JournalDocument, DocumentField, HistoryJournal
from dictionaries.models import Element
from users.models import User
from users.serializers import UserAVPSerializer
from rest_framework.response import Response
from rest_framework import status


STATUSES = {
    "created": "созданный",
    "review": "на согласовании подрядчика",
    "averment": "на утверждении подрядчика",
    "averment_abp": "на утверждении АБП",
    "review_root": "на согласовании заказчика",
    "averment_root": "на утверждении заказчика",
    "signed": "подписан",
    "cancelled": "отменено"}


class IndicatorValueSerializer(serializers.ModelSerializer):
    """
    Serializer for indicator values
    """
    indicator_meta = serializers.SerializerMethodField()
    indicator_value = serializers.SerializerMethodField()

    class Meta:
        model = FieldValue
        fields = ("id", "indicator_value", "indicator_meta")

    def get_indicator_meta(self, obj):
        if obj.indicator:
            indicator = obj.indicator
            return {"short_name": indicator.short_name, "type_value": indicator.type_value, "code": indicator.idc_code,
                    "reference": indicator.reference}

    def get_indicator_value(self, obj):
        if obj.indicator.type_value == "dct":
            short_name = Element.objects.get(id=obj.indicator_value).short_name
        else:
            short_name = obj.indicator_value
        return short_name


class JournalModelSerializer(serializers.ModelSerializer):
    # user = serializers.HiddenField(default=serializers.CurrentUserDefault()) для добавление автора автоматически
    # author = serializers.StringRelatedField(many=False)
    # abc_document = serializers.StringRelatedField(many=False)
    abc_document = serializers.CharField(source="abc_document.abc_code")
    field_value = IndicatorValueSerializer(many=True, read_only=True)

    class Meta:
        model = JournalDocument
        # fields = ("author", "created_at", "field_value")
        fields = ("abc_document", "field_value",)


class ParentJournalModelSerializer(serializers.ModelSerializer):
    field_value = IndicatorValueSerializer(many=True, read_only=True)
    abc_document = serializers.CharField(source="abc_document.abc_code")

    class Meta:
        model = JournalDocument
        fields = ("abc_document", "field_value")


class JournalModelVacancySerializer(serializers.ModelSerializer):
    vacancy = ParentJournalModelSerializer(source="parent", read_only=True)
    vacancy_stage = IndicatorValueSerializer(source="field_value", many=True, read_only=True)
    count_clicks = serializers.SerializerMethodField()

    class Meta:
        model = JournalDocument
        fields = ("author", "created_at", "count_clicks", "vacancy", "vacancy_stage")

    def get_count_clicks(self, obj):
        return JournalDocument.objects.filter(parent_id=obj.parent_id).count()


class JournalSerializer(serializers.Serializer):
    # user = serializers.HiddenField(default=serializers.CurrentUserDefault()) для добавление автора автоматически
    # journal = serializers.JSONField()
    # indicator = serializers.ListField()
    files = serializers.FileField()
    data = serializers.JSONField()

    def create(self, validated_data):
        user = self.required.user
        # journal_create(validated_data["journal"], validated_data["indicator"], user)
        return Response({"journal_id": "test"}, status=status.HTTP_200_OK)


class FieldSerializer(serializers.ModelSerializer):
    """
    Сериализатор для полей
    """
    parameters = serializers.SlugRelatedField(
        slug_field="short_name", queryset=IndicatorParameter.objects.all(), many=True)

    class Meta:
        model = DocumentField
        fields = ("id", "short_name", "idc_code", "type_value", "parameters", "reference")




class CategoryDocumentSerializer(serializers.ModelSerializer):
    """
    Сериализатор для категорий документов
    """
    children = serializers.SerializerMethodField()
    document = serializers.SerializerMethodField()

    class Meta:
        model = CategoryDocument
        fields = ("id", "short_name", "description",
                  "index_sort", "parent", "children", "document")

    def get_children(self, obj):
        """
        Функция для проверки дочерних категорий
        """
        children_qs = obj.children.all()
        if children_qs.exists():
            return True
        return False

    def get_document(self, obj):
        reports = ABCDocument.objects.filter(category_document=obj.id)
        if reports.exists():
            return True
        return False


class DocumentSerializer(serializers.ModelSerializer):
    """
    Сериализатор для документов
    """
    class Meta:
        model = ABCDocument
        fields = ("id", "naming", "description", "category_document")



class JournalHistorySerializer(serializers.ModelSerializer):
    """
    Serialize
    """
    # user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    author = serializers.CharField(source="author.get_full_name")
    status = serializers.SerializerMethodField()

    class Meta:
        model = HistoryJournal
        fields = ("status", "status_comment", "created_at", "author")

    def get_status(self, obj):
        return get_actual_status(obj.journal_status)

class JournalSerializer2(serializers.ModelSerializer):
    # user = serializers.HiddenField(default=serializers.CurrentUserDefault()) для добавление автора автоматически
    class Meta:
        model = JournalDocument
        fields = ("id", "short_name", "code")


class JournalSerializerOld(serializers.ModelSerializer):
    # user = serializers.HiddenField(default=serializers.CurrentUserDefault()) для добавление автора автоматически
    class Meta:
        model = JournalDocument
        fields = "__all__"

    # def create(self, validated_data):
    #     print("create validated_data", validated_data)
    #     return JournalDocument.objects.create(**validated_data)
    #
    # def update(self, instance, validated_data):
    #     print("update instance", instance)
    #     print("update validated_data", validated_data)
    #     instance.short_name = validated_data.get('short_name', instance.short_name)
    #     instance.save()
    #     return instance


class JournalDocumentSerializer(serializers.ModelSerializer):
    """
    Сериализатор для Elements
    """
    children = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    author = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = JournalDocument
        fields = ("id", "short_name", "code", "abc_document", "parent", "children",
                  "doc_number", "date_time", "status", "author")

    def get_status(self, obj):
        last_status = obj.history_status.last()
        if last_status:
            return JournalHistorySerializer(last_status).data

    def get_children(self, obj):
        """
        Функция для проверки дочерних категорий
        """
        children_qs = obj.children.all()
        if children_qs.exists():
            return True
        return False


class JournalDetailSerializer(serializers.ModelSerializer):
    """
    Сериализатор для Elements
    """
    children = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    indicator_value = serializers.SerializerMethodField()
    user = serializers.SerializerMethodField()

    class Meta:
        model = JournalDocument
        fields = ("id", "short_name", "code", "abc_document", "parent", "children",
                  "doc_number", "date_time", "status", "indicator_value", "user")

    # def to_representation(self, instance):
    #     data = super().to_representation(instance)
    #     request = self.context.get('request')
    #     if request and hasattr(request, 'user'):
    #         data["user_id"] = request.user.id
    #     return data

    def get_user(self, obj):
        request = self.context.get("request")
        user_object = User.objects.get(id=request.user.id)
        return UserAVPSerializer(user_object).data

    def get_indicator_value(self, obj):
        indicators = obj.journal_doc.all()
        return FieldValue2Serializer(indicators).data

    def get_status(self, obj):
        request = self.context.get("request")
        current_user_id = request.user.id
        last_status = obj.history_status.last()
        last_id = last_status.author_id
        if current_user_id == last_id:
            return JournalHistorySerializer(last_status).data
        # last_status = obj.history_status.filter(stage="point").last()
        last_status = obj.history_status.last()
        return JournalHistorySerializer(last_status).data

    def get_children(self, obj):
        """
        Функция для проверки дочерних категорий
        """
        children_qs = obj.children.all()
        if children_qs.exists():
            return True
        return False


class FieldSerializerOLD(serializers.ModelSerializer):
    """
    Сериализатор для полей
    """
    parameters = serializers.SlugRelatedField(
        slug_field="short_name", queryset=IndicatorParameter.objects.all(), many=True)

    class Meta:
        model = DocumentField
        fields = ("id", "short_name", "type_value", "parameters", "reference")


class FieldValueSerializer(serializers.ModelSerializer):
    """
    Сериализатор для значений полей
    """
    indicator_info = serializers.SerializerMethodField()
    indicator = serializers.SerializerMethodField()
    author = serializers.SerializerMethodField()
    act_id = serializers.SerializerMethodField()

    class Meta:
        model = FieldValue
        fields = ("journal_document_id", "indicator", "indicator_info", "author", "act_id")

    def get_act_id(self, obj):
        return obj.journal_document.parent.id if obj.journal_document.parent else None
    def get_author(self, obj):
        return obj.journal_document.author.id if obj.journal_document else None

    def get_indicator(self, obj):
        if obj.indicator.type_value in ("dct", "dcm"):
            short_name = Element.objects.values("short_name").get(id=obj.indicator_value)
        else:
            short_name = obj.indicator_value
        return short_name

    def get_indicator_info(self, obj):
        if obj.indicator:
            indicator = obj.indicator
            return {"short_name": indicator.short_name, "type_value": indicator.type_value}


class FieldValue2Serializer(serializers.ModelSerializer):
    """
    Сериализатор для значений полей
    """
    indicator = serializers.SerializerMethodField()

    class Meta:
        model = FieldValue
        fields = ("indicator",)

    def get_indicator(self, obj):
        result = []
        for i in obj:
            indicator = DocumentField.objects.get(id=i.indicator_id)
            if indicator.type_value == "dct":
                element = Element.objects.get(id=i.indicator_value)
                short_name = element.short_name
                element_id = element.id
                code = element.abc_dictionary.abc_code
            else:
                short_name = i.indicator_value
                code = indicator.idc_code
                element_id = None
            idc = {"id": i.id, "value": short_name, "element_id": element_id, "label": i.indicator.short_name,
                   "type": i.indicator.type_value, "code": code}
            result.append(idc)
        return result


def get_actual_status(status):
    return STATUSES.get(status)
