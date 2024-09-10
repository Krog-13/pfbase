from rest_framework.response import Response
from IEF.minio_client import MinioClient
from rest_framework import status
from uuid import uuid4
import logging.config
from .models import RecordIndicatorValue, Indicator

# init logging
logger = logging.getLogger("ief_logger")

minio = MinioClient()
minio.get_client()


def save_file_minio(files):
    files_naming = []
    if isinstance(files, list):
        for file in files:
            file_id = uuid4().hex
            file_data = f"{file.name},{file_id}"
            files_naming.append(file_data)
            minio.save_file_minio(file, file_id)
    else:
        file_id = uuid4().hex
        file_data = f"{files.name},{file_id}"
        files_naming.append(file_data)
        minio.save_file_minio(files, file_id)
    return files_naming


def upload_file(journal_id, string_path_file, code):
    try:
        indicator_id = Indicator.objects.get(idc_code=code)
    except Indicator.DoesNotExist:
        return Response({"Error msg": f"Code not found - {code}"}, status=status.HTTP_400_BAD_REQUEST)
    for file_data in string_path_file.split(";"):
        RecordIndicatorValue.objects.create(indicator_value=file_data,
                journal_document_id=journal_id,
                indicator_id=indicator_id.id)
    return Response({}, status=status.HTTP_201_CREATED)


def update_file(field_id, string_path_file):
    try:
        field_value = RecordIndicatorValue.objects.get(id=field_id)
    except RecordIndicatorValue.DoesNotExist:
        return Response({"message": f"File not found by id - {field_id}"}, status=status.HTTP_400_BAD_REQUEST)
    for file_data in string_path_file.split(";"):
        field_value.indicator_value = file_data
        field_value.save()
    return Response({"message": "File update success!"}, status=status.HTTP_200_OK)


def download_file(value_id):
    """
    Download file from minIO
    """
    try:
        file_name = RecordIndicatorValue.objects.get(id=value_id).indicator_value
    except RecordIndicatorValue.DoesNotExist:
        return Response({"Message": "file not found"}, status=status.HTTP_404_NOT_FOUND)
    file = file_name.split(',')
    if file:
        return minio.get_file_minio(file[1], file[0])  # file[1] - file_id, file[0] - file_name
    return Response({"Message": "file not found"}, status=status.HTTP_404_NOT_FOUND)
