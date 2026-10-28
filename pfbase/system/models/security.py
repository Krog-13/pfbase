import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


class AuthSession(models.Model):
    """At most one session row per user, shared by JWT and Django admin."""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    session_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_at = models.DateTimeField(default=timezone.now)
    last_activity_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField()
    revoked_at = models.DateTimeField(null=True, blank=True)
    revoke_reason = models.CharField(max_length=64, blank=True)
    credential_digest = models.CharField(max_length=64)
    kind = models.CharField(max_length=16, default='jwt')

    class Meta:
        db_table = '"stm"."auth_session"'


class RefreshCredential(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    session_id = models.UUIDField(db_index=True)
    digest = models.CharField(max_length=64, unique=True)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = '"stm"."refresh_credential"'


class PasswordResetCredential(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    digest = models.CharField(max_length=64, unique=True)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = '"stm"."password_reset_credential"'


class SecurityEvent(models.Model):
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                             on_delete=models.SET_NULL, related_name='security_events')
    actor_id = models.PositiveBigIntegerField(null=True, blank=True)
    subject_id = models.PositiveBigIntegerField(null=True, blank=True)
    event = models.CharField(max_length=64, db_index=True)
    result = models.CharField(max_length=16, default='success')
    reason = models.CharField(max_length=255, blank=True)
    address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        db_table = '"stm"."security_event"'
        ordering = ('-created_at', '-id')
