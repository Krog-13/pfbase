from django.core.mail import send_mail
import os
from rest_framework import serializers

class EmailSendNotification:
    """
    Email send notifications
    """
    @staticmethod
    def send_notification(subject, message, from_email, to, html_message=None):
        send_mail(subject, message, from_email, to, html_message=html_message)

ALLOWED_EXTENSIONS = ("jpg", "jpeg", "png", "svg", "pdf", "txt", "xml", "zip", "rar")

def validate_file_extension(file):
    extension = os.path.splitext(file.name)[1].lower().lstrip('.')

    if extension not in ALLOWED_EXTENSIONS:
        raise serializers.ValidationError(
            f"Недопустимое расширение файла: .{extension}."
            f"Разрешены {', '.join(ALLOWED_EXTENSIONS)}"
        )

    return file