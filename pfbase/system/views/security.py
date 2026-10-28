from django.db import transaction
from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed, ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import AccessToken

from ..models.user import User
from ..models.security import AuthSession
from ..security import (account_denial, audit, check_credentials,
                        issue_pair, new_session, refresh_pair, revoke_sessions, validated_session)


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=False)
    email = serializers.EmailField(required=False)
    password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate(self, attrs):
        if not (attrs.get('username') or attrs.get('email')):
            raise serializers.ValidationError('Username or email is required.')
        return attrs


class RefreshSerializer(serializers.Serializer):
    refresh = serializers.CharField(trim_whitespace=False)


class VerifySerializer(serializers.Serializer):
    token = serializers.CharField(trim_whitespace=False)


class PublicSecurityView(APIView):
    authentication_classes = ()
    permission_classes = (AllowAny,)

    def get_authenticate_header(self, request):
        return 'Bearer realm="api"'

    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        response['Cache-Control'] = 'no-store'
        response['Pragma'] = 'no-cache'
        return response


class SecurityTokenObtainView(PublicSecurityView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        checked = check_credentials(data.get('username') or data['email'], data['password'], request)
        if checked is None:
            raise AuthenticationFailed('Invalid credentials or account unavailable.')
        with transaction.atomic():
            user = User.objects.select_for_update().get(pk=checked.pk)
            if account_denial(user, request) or user.password != checked.password:
                raise AuthenticationFailed('Account state changed. Please sign in again.')
            session = new_session(user)
            return Response(issue_pair(user, session))


class SecurityTokenRefreshView(PublicSecurityView):
    def post(self, request):
        serializer = RefreshSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(refresh_pair(serializer.validated_data['refresh'], request))


class SecurityTokenVerifyView(PublicSecurityView):
    def post(self, request):
        serializer = VerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            token = AccessToken(serializer.validated_data['token'])
            user = User.objects.get(pk=token['user_id'])
        except (TokenError, KeyError, User.DoesNotExist, ValueError, TypeError):
            raise AuthenticationFailed('Invalid access token.')
        validated_session(user, token.get('sid'), request)
        return Response({})


class SessionActivityView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        # Only explicit foreground activity extends idle time. GETs and refresh do not.
        with transaction.atomic():
            user = User.objects.select_for_update().get(pk=request.user.pk)
            session = validated_session(user, request.auth.get('sid'), request)
            AuthSession.objects.filter(pk=session.pk, session_id=session.session_id).update(last_activity_at=timezone.now())
        return Response({'message': 'Activity recorded'})


class SessionLogoutView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        with transaction.atomic():
            user = User.objects.select_for_update().get(pk=request.user.pk)
            validated_session(user, request.auth.get('sid'), request)
            revoke_sessions(user, 'logout')
            audit('logout', user, request=request)
        return Response({'message': 'Signed out'})


class LogoutAllView(SessionLogoutView):
    # There is exactly one current session, so this also invalidates all its tokens.
    pass
