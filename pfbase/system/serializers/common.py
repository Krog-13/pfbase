from rest_framework.exceptions import ValidationError
from rest_framework import serializers, exceptions
from ..minio_client import MinioClient
from uuid import uuid4
from minio.error import S3Error

# Initialize MinioClient


class FileSaveSerializer(serializers.Serializer):
    file = serializers.FileField(required=True)

    def create(self, validated_data):
        try:
            minio = MinioClient()
            minio.get_client()
            file = validated_data['file']
            file_id = uuid4().hex
            file_data = f"{file.name},{file_id}"
            minio.save_file_minio(file, file_id)
            return file_data
        except ValidationError as e:
            raise exceptions.ValidationError({"error": str(e)})


class FileGetSerializer(serializers.Serializer):
    file_data = serializers.CharField(required=True)

    def fetch_file(self, file_data):
        try:
            minio = MinioClient()
            minio.get_client()
            file_data = file_data.split(",")
            file = minio.get_file_minio(file_data[0], file_data[1])
        except S3Error as e:
            raise exceptions.ValidationError({"error": str(e.code)})
        return file
