from rest_framework import serializers


class RecordQuerySerializer(serializers.Serializer):
    document_code = serializers.CharField()
    indicators_code = serializers.ListField(child=serializers.CharField(),
                                            required=False,
                                            default=list)
