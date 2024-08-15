from rest_framework.generics import ListAPIView, CreateAPIView, get_object_or_404, UpdateAPIView, RetrieveUpdateAPIView
from rest_framework.permissions import AllowAny
from rest_framework.viewsets import ViewSet, ModelViewSet
from .models import User, Organization
# from .common import get_user_ids, get_user_emails, set_notification
from .serializers import UserSerializer, RegisterSerializer, OrganizationSerializer, \
    UserProfileSerializer, EmailSerializer, PermissionSerializer, UpdatePasswordSerializer
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, IsAdminUser
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.views import APIView
from django.contrib.auth.models import Permission
from IEF.mail_notificatoin import send_approve_users
from .permissions import IsOwnerOrReadOnly, IsAdminReadOnly
from rest_framework.decorators import action
from .serializers import AuthTokenSerializer
from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.template.loader import render_to_string
from django.contrib.auth.tokens import default_token_generator

class RegisterUserApiView(CreateAPIView):
    """Registration View"""
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer
    def post(self, request):
        serializer = self.serializer_class(data=request.data,
                                           context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        if not user.is_active:
            current_site = get_current_site(request)
            email = user.email
            subject = "Verify Email"
            message_contents = {
                'request': request,
                'user': user,
                'domain': current_site.domain,
                'uid':urlsafe_base64_encode(force_bytes(user.pk)),
                'token':default_token_generator.make_token(user)
            }
            try:
                message = render_to_string('users/verify_email_message.html', message_contents)
                send_approve_users(subject, message, [email], content_subtype='html')
                return Response("Ссылка для подтверждения отправлена ​​на вашу электронную почту.", status=status.HTTP_200_OK)
            except:
                return Response("Неверный адрес электронной почты.", status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response("You already verified.", status=status.HTTP_400_BAD_REQUEST)


class ConfirmEmailView(APIView):
    permission_classes = (AllowAny,)

    def get(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except(TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None
        if user is not None and default_token_generator.check_token(user, token):
            user.is_active = True
            user.save()
            return Response('Ваш адрес электронной почты подтвержден.')   
        else:
            return Response('Не удалось подтвердить вашу электронную почту.')

class CustomAuthToken(ObtainAuthToken):
    """Customizing the ObtainAuthToken"""
    serializer_class = AuthTokenSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data,
                                           context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        token, created = Token.objects.get_or_create(user=user)
        roles = [gp.name for gp in user.groups.all()]
        return Response({
            "token": token.key,
            "email": user.email,
            "user_id": user.pk,
            "roles": roles
        })


class UserLogout(APIView):
    """Logout ObtainAuthToken"""
    def get(self, request, format=None):
        if request.user.is_anonymous:
            return Response({"message": "User not found"}, status=status.HTTP_400_BAD_REQUEST)
        request.user.auth_token.delete()
        return Response(status=status.HTTP_200_OK)


class UserProfileViewSet(ViewSet):
    """READ or UPDATE profile"""
    queryset = User.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = (IsAuthenticated, IsOwnerOrReadOnly)

    def retrieve(self, request):
        queryset = User.objects.all()
        user = get_object_or_404(queryset, pk=request.user.id)
        serializer = UserProfileSerializer(user)
        return Response(serializer.data)

    def update(self, request):
        queryset = User.objects.all()
        file = request.data.get('file')
        if file:
            request.data._mutable = True
            request.data['avatar'] = file
        user = get_object_or_404(queryset, pk=request.user.id)
        serializer = UserProfileSerializer(user, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):
        """ Update password """
        obj = get_object_or_404(User, pk=request.user.id)
        serializer = UpdatePasswordSerializer(obj, data=request.data)
        if serializer.is_valid():
            serializer.save(obj)
            obj.save()
            return Response({"message": "Password changed successfully"}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # ToDo: set reset/update password https://github.com/anexia-it/django-rest-passwordreset

# ======================================================================================================================

# class SendEmailView(APIView):
#
#     permission_classes = (IsAuthenticated,)
#
#     def post(self, request):
#         serializer = EmailSerializer(data=request.data)
#         user = request.user
#         if serializer.is_valid():
#             subject = serializer.data.get("subject")
#             message = serializer.data.get("message")
#             notification_message = serializer.data.get("notification_message")
#             recipient_list = serializer.validated_data["recipient_list"]
#             act_id = serializer.validated_data["act_id"]
#             emails = get_user_emails(recipient_list)
#             try:
#                 if emails:
#                     set_notification(recipient_list, notification_message, user, act_id)
#                     # ToDo uncomment after complete setting email configuration
#                     # send_notification_email(subject, message, emails)
#                     return Response({"message": "Email send successfully"}, status=status.HTTP_200_OK)
#                 return Response({"message": "Any User not found"}, status=status.HTTP_400_BAD_REQUEST)
#             except Exception as e:
#                 return Response({"message": str(e)}, status=status.HTTP_400_BAD_REQUEST)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserModelViewSet(ListAPIView):
    """
    API для пользователей
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_queryset(self):
        role = self.request.query_params.get('role')
        if role:
            return self.queryset.filter(groups__name=role)
        return self.queryset.all()


class UserRolesModelViewSet(APIView):
    """
    API для пользователей
    """
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        """
        GET запрос для получения полей по группе
        """
        user = request.user
        groups = [gp.name for gp in user.groups.all()]
        return Response({"roles": groups})


# class UserSignCurrentModelViewSet(ListAPIView):
#     """
#     API для пользователей
#     """
#     queryset = User.objects.all()
#     serializer_class = UserSerializer
#     permission_classes = (IsAuthenticated,)
#
#     def get_queryset(self):
#         """
#         GET запрос для получения организаций
#         """
#         queryset = super(UserSignCurrentModelViewSet, self).get_queryset()
#         journal_id = self.request.query_params.get("journal_id")
#         code = self.request.query_params.get("code")
#         users = get_user_ids(journal_id, code)
#         if users:
#             return queryset.filter(id__in=users[0].indicator_value.split(","))
#         return queryset.none()


class UserSignModelViewSet(ListAPIView):
    """
    API для пользователей
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        """
        GET запрос для получения организаций
        """
        queryset = super(UserSignModelViewSet, self).get_queryset()
        org = self.request.user.organization
        return queryset.filter(organization=org)


class OrganisationsAPIVIew(ListAPIView):
    """
    API для организаций
    """
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        """
        GET запрос для получения организаций
        """
        queryset = super(OrganisationsAPIVIew, self).get_queryset()
        if self.request.query_params.get("org_id"):
            return queryset.filter(id=self.request.query_params.get("org_id"))
        return super(OrganisationsAPIVIew, self).get_queryset()




class UserViewSet(ModelViewSet):
    """
    API для профиля пользователя
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (IsAuthenticated, IsAdminUser)

    # def retrieve(self, request):
    #     queryset = User.objects.all()
    #     user = get_object_or_404(queryset, pk=request.user.id)
    #     serializer = UserProfileSerializer(user)
    #     return Response(serializer.data)
    #
    # def update_user(self, request):
    #     queryset = User.objects.all()
    #     user = get_object_or_404(queryset, pk=request.user.id)
    #     serializer = UserProfileSerializer(user, data=request.data)
    #     if serializer.is_valid():
    #         serializer.save()
    #         return Response(serializer.data)
    #     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserPermissionAPIView(APIView):
    """
    GET запрос для получения прав пользователя
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        permissions = Permission.objects.filter(user=request.user)
        serializer = PermissionSerializer(permissions, many=True)
        return Response(serializer.data)