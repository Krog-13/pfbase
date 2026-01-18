from django.core.mail import send_mail
import os
from rest_framework import serializers
import filetype

class EmailSendNotification:
    """
    Email send notifications
    """
    @staticmethod
    def send_notification(subject, message, from_email, to, html_message=None):
        send_mail(subject, message, from_email, to, html_message=html_message)



ALLOWED_EXTENSIONS = ("jpg", "jpeg", "png", "pdf", "docx", "xlsx", "txt")
# EXTENSION_TO_MIME = {
#     "jpg": ["image/jpeg"],
#     "jpeg": ["image/jpeg"],
#     "png": ["image/png"],
#     "pdf": ["application/pdf"],
#     "docx": ["application/vnd.openxmlformats-officedocument.wordprocessingml.document"],
#     "xlsx": ["application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"],
#     "txt": ["text/plain", "text/x-plain"],
# }
EXTENSION_TO_FILETYPE = {
    "jpg": ["jpg"],
    "jpeg": ["jpg"],
    "png": ["png"],
    "pdf": ["pdf"],
    "docx": ["zip"],
    "xlsx": ["zip"],
}
MAX_SIZE_BY_EXTENSION = {
    "jpg": 20 * 1024 * 1024,
    "jpeg": 20 * 1024 * 1024,
    "png": 20 * 1024 * 1024,
    "pdf": 80 * 1024 * 1024,
    "docx": 80 * 1024 * 1024,
    "xlsx": 80 * 1024 * 1024,
    "txt": 40 * 1024 * 1024,
}
FORBIDDEN_FILENAME_PARTS = ("../", "..\\", "\x00")

class FileValidationService:
    @classmethod
    def validate(cls, file):
        cls.validate_size(file)
        cls.validate_filename(file)
        extension = cls.validate_extension(file)
        detected_type = cls.detect_real_type(file)
        cls.validate_type_vs_extension(file, extension, detected_type)
        # detected_mime = cls.detect_real_mime(file)
        # cls.validate_mime_vs_extension(extension, detected_mime)
        return file

    @classmethod
    def validate_size(cls, file):
        if file.size == 0:
            raise serializers.ValidationError({
                "file": file.name,
                "error": "File is empty"
            })

        extension = cls._get_extension(file)
        max_size = MAX_SIZE_BY_EXTENSION.get(extension)

        if max_size and file.size > max_size:
            raise serializers.ValidationError({
                "file": file.name,
                "error": f"File is too large. Maximum {max_size // (1024 * 1024)} MB"
            })

    @classmethod
    def validate_filename(cls, file):
        name = file.name

        if len(name) > 255:
            raise serializers.ValidationError({
                "file": file.name,
                "error": "File name too long"
            })

        for part in FORBIDDEN_FILENAME_PARTS:
            if part in name:
                raise serializers.ValidationError({
                    "file": file.name,
                    "error": "Invalid file name"
                })

    @classmethod
    def validate_extension(cls, file):
        extension = cls._get_extension(file)

        if extension not in ALLOWED_EXTENSIONS:
            raise serializers.ValidationError({
                "file": file.name,
                "error": f"Invalid file extension: .{extension}. "
                         f"Allowed extensions {', '.join(ALLOWED_EXTENSIONS)}"
            })

        return extension

    # @classmethod
    # def detect_real_mime(cls, file):
    #     header = file.read(2048)
    #     file.seek(0)
    #
    #     mime = magic.from_buffer(header, mime=True)
    #     return mime

    # @classmethod
    # def validate_mime_vs_extension(cls, extension, detected_mime):
    #     allowed_mimes = EXTENSION_TO_MIME.get(extension)
    #
    #     if not allowed_mimes:
    #         raise serializers.ValidationError(f"Неизвестный тип файла. Разрешены {','.join(ALLOWED_EXTENSIONS)} типы файлов")
    #     if detected_mime not in allowed_mimes:
    #         raise serializers.ValidationError(f"Тип файла не соответствует расширению ({detected_mime})")

    @classmethod
    def detect_real_type(cls, file):
        header = file.read(261)
        file.seek(0)

        kind = filetype.guess(header)

        if kind is None:
            raise serializers.ValidationError({
                "file": file.name,
                "error": "Unable to determine file type"
            })

        return kind.extension

    @classmethod
    def validate_type_vs_extension(cls, file, extension, detected_type):
        if extension == 'txt':
            return

        allowed_types = EXTENSION_TO_FILETYPE.get(extension)

        if not allowed_types:
            raise serializers.ValidationError({
                "file": file.name,
                "error": "Unknown file type"
            })

        if detected_type not in allowed_types:
            raise serializers.ValidationError({
                "file": file.name,
                "error": f"The file type does not match the extension {detected_type}"
            })

    @staticmethod
    def _get_extension(file):
        return os.path.splitext(file.name)[1].lower().lstrip(".")