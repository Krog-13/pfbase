from rest_framework import status, exceptions as exc
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from ..serializers.common import FileSaveSerializer, FileGetSerializer, FilesSaveSerializer
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework import views
import smtplib


from ..throttles import FileUploadThrottle


# from pfbase.system.kalkan_adapter import KalkanAdapter
# from pykalkan import enums


class FileAPIView(views.APIView):
    """
    File API View
    """
    permission_classes = [IsAuthenticated]
    throttle_classes = [FileUploadThrottle]
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


class MailCheckAPI(views.APIView):
    """
    Mail Check API View
    Проверяет возможность входа по SMTP.
    """
    def post(self, request):
        data = request.data
        # Получаем параметры из запроса
        email_host = data.get("email_host")
        email_port = data.get("email_port", 587)
        email_user = data.get("email_user")
        email_password = data.get("email_password")
        use_ssl = data.get("use_ssl", False)
        use_tls = data.get("use_tls", True)

        if not all([email_host, email_port, email_user, email_password]):
            return Response({"status": "error", "message": "Missing required parameters"},
                            status=status.HTTP_400_BAD_REQUEST)
        try:
            if use_ssl:
                server = smtplib.SMTP_SSL(email_host, email_port, timeout=10)
            else:
                server = smtplib.SMTP(email_host, email_port, timeout=10)
                if use_tls:
                    server.starttls()
            server.login(email_user, email_password)
            server.quit()
            return Response({
                "email": email_user,
                "status": "success",
                "message": "Login successful ✅"
            }, status=status.HTTP_200_OK)

        except smtplib.SMTPAuthenticationError as e:
            return Response({
                "email": email_user,
                "status": "failed",
                "message": "Login failed ❌",
                "error": str(e)
            }, status=status.HTTP_401_UNAUTHORIZED)
        except Exception as e:
            return Response({
                "email": email_user,
                "status": "error",
                "message": "Other error ❌",
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
# class EcpAPIView(views.APIView):
#     """
#     ECP API View
#     """
#     def post(self, request):
#         """Verify ECP signature and validate certificate via OCSP"""
#         signature = request.data.get("signature")
#         data = request.data.get("data")
#
#         code_1 = enums.CertProp.KC_SUBJECT_SERIALNUMBER
#         code_2 = enums.CertProp.KC_SUBJECT_SURNAME
#
#         serializer = FileSaveSerializer(data=request.data)
#         if not signature or not data:
#             raise exc.ValidationError({"message": "Signature and data are required."})
#
#         if serializer.is_valid():
#             adapter = KalkanAdapter()
#             try:
#                 adapter.verify_data(signature, data, cert_code=[code_1, code_2])
#
#                 return Response({"message": "Signature verified successfully."},
#                                 status=status.HTTP_200_OK)
#             except Exception as e:
#                 raise exc.ValidationError({"message": str(e)})
#         raise exc.ValidationError(serializer.errors)
