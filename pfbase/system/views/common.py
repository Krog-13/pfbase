from rest_framework import status, exceptions as exc
from rest_framework.response import Response
from rest_framework import views
from ..serializers.common import FileSaveSerializer, FileGetSerializer, FilesSaveSerializer
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser


class FileAPIView(views.APIView):
    """
    File API View
    """
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get(self, request):
        """Get file from minio"""
        file_data = request.query_params.get("file_data")
        serializer = FileGetSerializer(data={"file_data": file_data})
        if serializer.is_valid():
            file = serializer.fetch_file(file_data)
            return file
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def post(self, request):
        """Save file in minio"""
        if request.data.get("file"):
            serializer = FileSaveSerializer(data=request.data)
            if serializer.is_valid():
                file_data = serializer.save()
                return Response({"message": "File saved in minio storage", "file_data": file_data},
                                status=status.HTTP_201_CREATED)
            raise exc.ValidationError(serializer.errors)

        elif request.data.get("files"):
            serializer = FilesSaveSerializer(data=request.data)
            if serializer.is_valid():
                file_data = serializer.save()
                return Response({"message": "Files saved in minio storage", "file_data": file_data},
                                status=status.HTTP_201_CREATED)
            raise exc.ValidationError(serializer.errors)
        else:
            raise exc.ValidationError({"message": "Failed to process the uploaded file(s). Please try again or check the file format."})
