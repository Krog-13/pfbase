from django.contrib.auth.models import AbstractUser
from django.db import models

from .organization import Organization


class User(AbstractUser):
    """
    Users of the system
    """
    avatar = models.ImageField(upload_to='avatars/', verbose_name='Profile photo', null=True, blank=True)
    organization = models.ForeignKey(
        to=Organization, on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name='Organization', related_name='users')

    def __str__(self):
        return self.username

    class Meta:
        db_table = '"stm\".\"users"'
        verbose_name = 'STM User'
        verbose_name_plural = 'STM Users'
