from django.contrib.auth.models import AbstractUser, Group
from django.db import models
from .organization import Organization


class User(AbstractUser):
    """
    Пользователь
    """
    avatar = models.ImageField(upload_to='avatars/', verbose_name='Фото профиля', null=True, blank=True)
    organization = models.ForeignKey(
        to=Organization, on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name='Организация', related_name='users')

    def __str__(self):
        return self.username

    class Meta:
        db_table = '"stm\".\"users"'
        verbose_name = 'STM Пользователь'
        verbose_name_plural = 'STM Пользователи'
