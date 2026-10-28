"""Database-backed account policy. Never store raw passwords or bearer tokens."""
import hashlib
import ipaddress
import json
import secrets
from contextvars import ContextVar
from datetime import datetime, timedelta, timezone as dt_timezone

from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from django.utils.crypto import constant_time_compare, salted_hmac
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from .models.user import User
from .models.security import AuthSession, PasswordResetCredential, RefreshCredential, SecurityEvent

current_request = ContextVar('security_request', default=None)


def policy(name):
    return settings.ACCOUNT_SECURITY[name]


def token_digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


def audit(event, user=None, *, reason='', result='success', request=None):
    request = request or current_request.get()
    actor = getattr(request, 'user', None)
    address = getattr(request, 'META', {}).get('REMOTE_ADDR')
    try:
        address = str(ipaddress.ip_address(address)) if address else None
    except ValueError:
        address = None
    SecurityEvent.objects.create(user=user, subject_id=user.pk if user else None,
                                 actor_id=actor.pk if actor and actor.is_authenticated else None,
                                 event=event, reason=reason, result=result, address=address)


def credential_digest(user):
    # Query fresh permissions: a cached Django user permission set is insufficient.
    permissions = list(user.user_permissions.order_by('pk').values_list('pk', 'codename', 'content_type__app_label'))
    groups = list(user.groups.order_by('pk').values_list('pk', flat=True))
    group_permissions = list(user.groups.order_by('pk', 'permissions__pk').values_list(
        'pk', 'permissions__pk', 'permissions__codename', 'permissions__content_type__app_label'))
    values = [user.password, user.username, user.email, user.is_active, user.is_staff,
              user.is_superuser, str(user.expires_at), str(user.locked_until),
              str(user.password_changed_at), user.access_rules, permissions, groups, group_permissions]
    return salted_hmac('account-session', json.dumps(values, sort_keys=True), algorithm='sha256').hexdigest()


def validate_access_rules(value):
    if not isinstance(value, dict) or set(value) - {'networks', 'weekdays', 'start', 'end'}:
        raise ValidationError('Invalid access rules.')
    try:
        if 'networks' in value:
            if not isinstance(value['networks'], list):
                raise ValueError
            for network in value['networks']:
                ipaddress.ip_network(network)
        if 'weekdays' in value and (not isinstance(value['weekdays'], list) or
                any(type(day) is not int or not 0 <= day <= 6 for day in value['weekdays'])):
            raise ValueError
        if ('start' in value) != ('end' in value):
            raise ValueError
        for name in ('start', 'end'):
            if name in value:
                datetime.strptime(value[name], '%H:%M')
    except (ValueError, TypeError):
        raise ValidationError('Invalid access rules.')


def account_denial(user, request=None):
    now = timezone.now()
    if not user.is_active:
        return 'account_disabled'
    if user.expires_at and user.expires_at <= now:
        return 'account_expired'
    if user.locked_until and user.locked_until > now:
        return 'account_locked'
    if user.password_changed_at + timedelta(seconds=policy('PASSWORD_MAX_AGE')) <= now:
        return 'password_expired'
    rules = user.access_rules
    try:
        validate_access_rules(rules)
    except ValidationError:
        return 'invalid_access_rules'
    utc_now = now.astimezone(dt_timezone.utc)
    if 'weekdays' in rules and utc_now.weekday() not in rules['weekdays']:
        return 'access_schedule'
    if 'start' in rules:
        start, end = (datetime.strptime(rules[name], '%H:%M').time() for name in ('start', 'end'))
        current = utc_now.time().replace(tzinfo=None)
        allowed = start <= current < end if start < end else (current >= start or current < end)
        if not allowed:
            return 'access_schedule'
    if 'networks' in rules:
        try:
            address = ipaddress.ip_address(getattr(request, 'META', {}).get('REMOTE_ADDR', ''))
            if not any(address in ipaddress.ip_network(network) for network in rules['networks']):
                return 'access_network'
        except ValueError:
            return 'access_network'
    return ''


def revoke_sessions(user, reason):
    count = AuthSession.objects.filter(user=user, revoked_at__isnull=True).update(
        revoked_at=timezone.now(), revoke_reason=reason)
    if count:
        audit('session_revoked', user, reason=reason)


def check_credentials(identifier, password, request=None):
    """Return None on failure, committing lock counters BEFORE the caller raises."""
    from django.db.models import Q
    with transaction.atomic():
        # Ambiguous email/username is rejected rather than choosing an account.
        users = list(User.objects.select_for_update().filter(
            Q(username__iexact=identifier) | Q(email__iexact=identifier)).order_by('pk')[:2])
        if len(users) != 1:
            User().set_password(password)  # Match the password-hasher cost for unknown users.
            audit('login_failed', result='failure', reason='invalid_credentials', request=request)
            return None
        user = users[0]
        denial = account_denial(user, request)
        if denial:
            audit('login_failed', user, result='failure', reason=denial, request=request)
            return None
        if user.locked_until and user.locked_until <= timezone.now():
            user.failed_login_attempts = 0
            user.locked_until = None
            user.block_reason = ''
        if not user.check_password(password):
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= policy('MAX_FAILED_ATTEMPTS'):
                user.locked_until = timezone.now() + timedelta(seconds=policy('LOCK_SECONDS'))
                user.block_reason = 'failed_login_attempts'
                revoke_sessions(user, 'account_locked')
                audit('account_locked', user, reason='failed_login_attempts', request=request)
            # Do not use save(): counters must not invalidate on each failed attempt.
            User.objects.filter(pk=user.pk).update(failed_login_attempts=user.failed_login_attempts,
                locked_until=user.locked_until, block_reason=user.block_reason)
            audit('login_failed', user, result='failure', reason='invalid_credentials', request=request)
            return None
        User.objects.filter(pk=user.pk).update(failed_login_attempts=0, locked_until=None, block_reason='')
        user.failed_login_attempts, user.locked_until, user.block_reason = 0, None, ''
        return user


def new_session(user, kind='jwt'):
    # Caller holds the user row lock; OneToOne also enforces the limit in the DB.
    import uuid
    now = timezone.now()
    revoke_sessions(user, 'new_login')
    session, _ = AuthSession.objects.update_or_create(user=user, defaults={
        'session_id': uuid.uuid4(), 'created_at': now, 'last_activity_at': now,
        'expires_at': now + timedelta(seconds=policy('SESSION_MAX_AGE')),
        'revoked_at': None, 'revoke_reason': '', 'credential_digest': credential_digest(user), 'kind': kind})
    audit('session_issued', user, reason=kind)
    audit('login', user)
    User.objects.filter(pk=user.pk).update(last_login=now)
    return session


def issue_pair(user, session):
    refresh = RefreshToken.for_user(user)
    refresh['sid'] = str(session.session_id)
    # Rotation does not extend the absolute session expiry.
    refresh['exp'] = min(refresh['exp'], int(session.expires_at.timestamp()))
    access = refresh.access_token
    access['exp'] = min(access['exp'], refresh['exp'])
    encoded = str(refresh)
    RefreshCredential.objects.create(user=user, session_id=session.session_id,
        digest=token_digest(encoded), expires_at=datetime.fromtimestamp(refresh['exp'], dt_timezone.utc))
    audit('token_issued', user)
    return {'access': str(access), 'refresh': encoded}


def session_denial(user, session, request=None):
    now = timezone.now()
    if session.revoked_at:
        return 'session_revoked'
    if session.expires_at <= now:
        return 'session_expired'
    if session.last_activity_at + timedelta(seconds=policy('IDLE_SECONDS')) <= now:
        return 'session_idle'
    denial = account_denial(user, request)
    if denial:
        return denial
    if not constant_time_compare(session.credential_digest, credential_digest(user)):
        return 'credentials_changed'
    return ''


def validated_session(user, sid, request=None):
    try:
        session = AuthSession.objects.get(user=user, session_id=sid)
    except (AuthSession.DoesNotExist, ValidationError, ValueError, TypeError):
        raise AuthenticationFailed('Session is invalid.', code='session_invalid')
    denial = session_denial(user, session, request)
    if denial:
        # Match sid, so a delayed request cannot revoke a newer login.
        changed = AuthSession.objects.filter(pk=session.pk, session_id=sid, revoked_at__isnull=True).update(
            revoked_at=timezone.now(), revoke_reason=denial)
        if changed:
            audit('session_revoked', user, reason=denial, request=request)
        raise AuthenticationFailed('Session is no longer valid.', code=denial)
    return session


def refresh_pair(encoded, request=None):
    try:
        token = RefreshToken(encoded)
        user_id, sid = token['user_id'], token['sid']
    except (TokenError, KeyError, TypeError):
        raise AuthenticationFailed('Invalid refresh token.')
    error, result = None, None
    with transaction.atomic():
        user = User.objects.select_for_update().filter(pk=user_id).first()
        if user is None:
            error = 'Invalid refresh token.'
        else:
            credential = RefreshCredential.objects.filter(user=user, digest=token_digest(encoded)).first()
            if not credential or credential.expires_at <= timezone.now():
                error = 'Invalid refresh token.'
            elif credential.used_at:
                session = AuthSession.objects.filter(user=user, session_id=credential.session_id).first()
                if session:
                    revoke_sessions(user, 'refresh_reused')
                audit('token_reused', user, reason='refresh', result='failure', request=request)
                error = 'Refresh token has already been used.'
            else:
                try:
                    session = validated_session(user, sid, request)
                except AuthenticationFailed:
                    error = 'Session is no longer valid.'
                else:
                    credential.used_at = timezone.now()
                    credential.save(update_fields=['used_at'])
                    result = issue_pair(user, session)
    if error:
        raise AuthenticationFailed(error)
    return result


def create_reset(user):
    now = timezone.now()
    PasswordResetCredential.objects.filter(user=user, used_at__isnull=True).update(used_at=now)
    token = secrets.token_urlsafe(32)
    PasswordResetCredential.objects.create(user=user, digest=token_digest(token),
        expires_at=now + timedelta(seconds=policy('RESET_SECONDS')))
    audit('password_reset_requested', user)
    return token


def reset_password(uid, token, password, request=None):
    error = None
    with transaction.atomic():
        user = User.objects.select_for_update().filter(pk=uid).first()
        credential = PasswordResetCredential.objects.filter(user=user, digest=token_digest(token)).first() if user else None
        if not credential or credential.expires_at <= timezone.now():
            error = 'Invalid or expired reset link.'
        elif credential.used_at:
            audit('token_reused', user, reason='password_reset', result='failure', request=request)
            error = 'Invalid or expired reset link.'
        elif not user.is_active or (user.expires_at and user.expires_at <= timezone.now()):
            error = 'Account is unavailable.'
        else:
            validate_password(password, user=user)
            user.set_password(password)
            user.save(update_fields=['password'])
            PasswordResetCredential.objects.filter(user=user, used_at__isnull=True).update(used_at=timezone.now())
            audit('password_reset', user, request=request)
    if error:
        raise ValidationError(error)
