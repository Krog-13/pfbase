from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db import transaction
from django.utils import timezone
from .organization import Organization


class User(AbstractUser):
    """
    Users of the system
    """
    avatar = models.ImageField(upload_to='avatars/', verbose_name='Profile photo', null=True, blank=True)
    organization = models.ForeignKey(
        to=Organization, on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name='Organization', related_name='users')
    expires_at = models.DateTimeField(null=True, blank=True)
    locked_until = models.DateTimeField(null=True, blank=True)
    block_reason = models.CharField(max_length=255, blank=True)
    failed_login_attempts = models.PositiveIntegerField(default=0)
    password_changed_at = models.DateTimeField(default=timezone.now, editable=False)
    access_rules = models.JSONField(default=dict, blank=True,
                                  help_text='Optional networks (CIDR), weekdays (0-6), start/end (HH:MM, UTC).')

    def save(self, *args, **kwargs):
        # Keep these imports local: security imports User during Django startup.
        from ..security import audit, revoke_sessions
        from .security import PasswordResetCredential

        # Serialize credential changes with login, reset and refresh operations.

        tracked = ('password', 'is_active', 'is_staff', 'is_superuser', 'username',
                   'email', 'expires_at', 'locked_until', 'access_rules')
        using = kwargs.get('using') or self._state.db or 'default'
        with transaction.atomic(using=using):
            previous = type(self).objects.using(using).select_for_update().filter(pk=self.pk).first() if self.pk else None
            update_fields = kwargs.get('update_fields')
            changed = [name for name in tracked if previous and
                       (update_fields is None or name in update_fields) and
                       getattr(previous, name) != getattr(self, name)]
            if 'password' in changed:
                self.password_changed_at = timezone.now()
                if update_fields is not None:
                    kwargs['update_fields'] = set(update_fields) | {'password_changed_at'}
            super().save(*args, **kwargs)
            if changed:
                revoke_sessions(self, 'credentials_changed')
                if {'password', 'email', 'is_active'}.intersection(changed):
                    PasswordResetCredential.objects.filter(user=self, used_at__isnull=True).update(used_at=timezone.now())
                audit('account_updated', self, reason=','.join(changed))
                if 'password' in changed:
                    audit('password_changed', self)
            elif previous is None:
                audit('account_created', self)

    def __str__(self):
        return self.username

    def clean(self):
        # Import after Django has finished loading model classes.
        from ..security import validate_access_rules

        super().clean()
        validate_access_rules(self.access_rules)

    class Meta:
        db_table = '"stm\".\"users"'
        verbose_name = 'STM User'
        verbose_name_plural = 'STM Users'
        permissions = [('manage_account_security', 'Can manage account security attributes')]
