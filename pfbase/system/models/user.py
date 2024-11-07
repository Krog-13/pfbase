from django.contrib.auth.models import AbstractUser, Group
from django.db import models
from .organization import Organization


class User(AbstractUser):
    """
    Пользователь
    """
    groups = models.ManyToManyField(
        Group,
        related_name="custom_user_set",
        blank=True,
        help_text="Группы, к которым принадлежит этот пользователь.",
        verbose_name="группы",
    )
    first_name = models.CharField(max_length=50, blank=True, null=True)
    last_name = models.CharField(max_length=50, blank=True, null=True)
    username = models.CharField(max_length=128, verbose_name='Пользователь', unique=True, null=False, blank=True)
    avatar = models.ImageField(upload_to='users', verbose_name='Фото профиля', null=True, blank=True)
    is_blocked = models.BooleanField(default=False, verbose_name='Заблокирован')
    organization = models.ForeignKey(
        to=Organization, on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name='Организация', related_name='users')

    def __str__(self):
        return f"{self.username} ({self.email})"

    class Meta:
        db_table = '"stm\".\"users"'
        verbose_name = 'STM Пользователь'
        verbose_name_plural = 'STM Пользователи'
