from rest_framework import status, exceptions as exc
from rest_framework.response import Response
from rest_framework import views
from ..serializers.common import FileSaveSerializer, FileGetSerializer, FilesSaveSerializer
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from pfbase.system.kalkan_adapter import KalkanAdapter
from pykalkan import enums


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


class EcpAPIView(views.APIView):
    """
    ECP API View
    """
    def post(self, request):
        """Verify ECP signature and validate certificate via OCSP"""
        signature = request.data.get("signature")
        data = request.data.get("data")

        code_1 = enums.CertProp.KC_SUBJECT_SERIALNUMBER
        code_2 = enums.CertProp.KC_SUBJECT_SURNAME

        serializer = FileSaveSerializer(data=request.data)
        if not signature or not data:
            raise exc.ValidationError({"message": "Signature and data are required."})

        if serializer.is_valid():
            adapter = KalkanAdapter()
            try:
                adapter.verify_data(signature, data, cert_code=[code_1, code_2])

                return Response({"message": "Signature verified successfully."},
                                status=status.HTTP_200_OK)
            except Exception as e:
                raise exc.ValidationError({"message": str(e)})
        raise exc.ValidationError(serializer.errors)
