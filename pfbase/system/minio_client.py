from django.conf import settings
from django.http import FileResponse
from urllib.parse import quote
from minio import Minio
import logging.config
import io

# init logging
logger = logging.getLogger("ief_logger")


class MinioClient:
    def __init__(self):
        self.client = None

    def get_client(self):
        logger.info("MinIO client initialization")
        self.client = Minio(
            endpoint=settings.MINIO_SERVER,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=False)
        return self.client

    def save_file_minio(self, file, file_id):
        """
        Функция для сохранения файла в minio
        """
        metadata = {"original-filename": file.name}
        byte_io = io.BytesIO(file.read())
        self.client.put_object(settings.MINIO_BUCKET, file_id, byte_io,
                               len(byte_io.getvalue()), metadata=metadata)
        logger.warning(f"Free form file saved in minio by file_id-{file_id}")

    def get_file_minio(self, file_id):
        """
        Retrieve file from minio
        """
        stat = self.client.stat_object(settings.MINIO_BUCKET, file_id)
        original_filename = stat.metadata.get("X-Amz-Meta-Original-Filename", "filename")
        data_object = self.client.get_object(bucket_name=settings.MINIO_BUCKET, object_name=file_id)
        headers = {"Content-Type": "multipart/byteranges", "Access-Control-Expose-Headers": "Content-Disposition",
                   "Content-Disposition": f"attachment; filename*=utf-8''{quote(original_filename)}"}
        return FileResponse(data_object, as_attachment=True, filename=original_filename, headers=headers)

    def delete_file_minio(self, file_id):
        """
        Delete file from minio
        """
        self.client.remove_object(settings.MINIO_BUCKET, file_id)
        logger.warning(f"Free form file deleted from minio by file_id-{file_id}")
