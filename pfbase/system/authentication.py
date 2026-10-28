from django.contrib.auth.backends import ModelBackend
from django.db import transaction
from django.http import HttpResponseForbidden
from django.contrib.auth import logout
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication

from .models.user import User
from .security import check_credentials, current_request, validated_session


class AccountBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        if password is None or not (username or kwargs.get('email')):
            return None
        return check_credentials(username or kwargs['email'], password, request)


class SessionJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        result = super().authenticate(request)
        if result:
            user, token = result
            validated_session(user, token.get('sid'), request)
        return result


class AccountSessionMiddleware:
    """Django admin uses the same single-session and expiry rules as the API."""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        context = current_request.set(request)
        try:
            if request.user.is_authenticated:
                try:
                    validated_session(request.user, request.session.get('security_sid'), request)
                except AuthenticationFailed:
                    logout(request)
                    return HttpResponseForbidden('Session expired. Please sign in again.')
                # Admin form submissions represent actions; background GET polling does not.
                if request.path.startswith('/admin/') and request.method == 'POST':
                    from django.utils import timezone
                    from .models.security import AuthSession
                    with transaction.atomic():
                        user = User.objects.select_for_update().get(pk=request.user.pk)
                        session = validated_session(user, request.session.get('security_sid'), request)
                        AuthSession.objects.filter(pk=session.pk, session_id=session.session_id).update(last_activity_at=timezone.now())
            return self.get_response(request)
        finally:
            current_request.reset(context)
