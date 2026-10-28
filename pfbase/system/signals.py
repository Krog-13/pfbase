from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models.signals import m2m_changed, pre_delete
from django.dispatch import receiver

from .models.security import AuthSession
from .security import account_denial, audit, new_session, revoke_sessions

User = get_user_model()


@receiver(user_logged_in)
def browser_login(sender, request, user, **kwargs):
    with transaction.atomic():
        user = User.objects.select_for_update().get(pk=user.pk)
        if account_denial(user, request):
            request.session.flush()
            raise PermissionDenied('Account unavailable.')
        session = new_session(user, 'browser')
        request.session['security_sid'] = str(session.session_id)


@receiver(user_logged_out)
def browser_logout(sender, request, user, **kwargs):
    if user and request:
        # An obsolete browser session must not revoke a more recent JWT login.
        with transaction.atomic():
            user = User.objects.select_for_update().filter(pk=user.pk).first()
            if user:
                session = AuthSession.objects.filter(user=user, session_id=request.session.get('security_sid')).first() if request.session.get('security_sid') else None
                if session:
                    revoke_sessions(user, 'logout')
                audit('logout', user, request=request)


@receiver(m2m_changed)
def permission_changes(sender, instance, action, reverse, pk_set, **kwargs):
    if sender not in (User.groups.through, User.user_permissions.through, Group.permissions.through):
        return
    if action.startswith('pre_'):
        if isinstance(instance, User):
            users = [instance.pk]
        elif sender == Group.permissions.through:
            if isinstance(instance, Group):
                users = list(User.objects.filter(groups=instance).values_list('pk', flat=True))
            else:
                group_ids = pk_set if pk_set is not None else instance.group_set.values_list('pk', flat=True)
                users = list(User.objects.filter(groups__pk__in=group_ids).values_list('pk', flat=True))
        else:
            users = list(pk_set) if pk_set is not None else list(instance.user_set.values_list('pk', flat=True))
        instance._security_affected_users = set(users)
    elif action.startswith('post_'):
        for user in User.objects.filter(pk__in=getattr(instance, '_security_affected_users', set())):
            revoke_sessions(user, 'permissions_changed')
            audit('account_permissions_changed', user, reason=action)


@receiver(pre_delete, sender=User)
def account_deleted(sender, instance, **kwargs):
    audit('account_deleted', instance)


@receiver(pre_delete, sender=Group)
def group_deleted(sender, instance, **kwargs):
    for user in instance.user_set.all():
        revoke_sessions(user, 'permissions_changed')
        audit('account_permissions_changed', user, reason='group_deleted')
