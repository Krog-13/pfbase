from rest_framework import serializers
from ..models.notification import Notification


class NotificationSerializer(serializers.ModelSerializer):
    read_at = serializers.DateTimeField(format="%d.%m.%Y %H:%M")
    created_at = serializers.DateTimeField(format="%d.%m.%Y %H:%M")

    class Meta:
        model = Notification
        fields = "__all__"

class NotificationShortSerializer(serializers.ModelSerializer):

    class Meta:
        model = Notification
        fields = "title", "message", "is_read", "type_notification"
