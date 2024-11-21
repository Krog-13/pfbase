from rest_framework import status, exceptions as exc
from rest_framework.response import Response
from rest_framework import views
from ..serializers.common import FileSaveSerializer, FileGetSerializer
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser


class FileAPIView(views.APIView):
    """
    File API View
    """
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get(self, request):
        """Get file from minio"""
        file_id = request.query_params.get("file_id")
        serializer = FileGetSerializer(data={"file_id": file_id})
        if serializer.is_valid():
            file = serializer.fetch_file(file_id)
            return file
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def post(self, request):
        """Save file in minio"""
        serializer = FileSaveSerializer(data=request.data)
        if serializer.is_valid():
            file_data = serializer.save()
            return Response({"message": "File saved in minio storage", "file_id": file_data},
                            status=status.HTTP_201_CREATED)
        raise exc.ValidationError(serializer.errors)
