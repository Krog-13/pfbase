from django.db import models
from django.contrib.auth.models import AbstractUser


class Organization(models.Model):
    """
    Structures of organization
    """
    short_name = models.CharField(max_length=255, unique=True, verbose_name='Наименование организации')
    identifier = models.CharField(max_length=128, null=True, blank=True, verbose_name='БИН')
    address = models.CharField(max_length=128, null=True, blank=True, verbose_name='Адрес')
    subsidiaries = models.ForeignKey("self", on_delete=models.CASCADE, null=True, blank=True, verbose_name='Филиалы')

    class Meta:
        verbose_name = "Организация"
        verbose_name_plural = "Организации"

    def __str__(self):
        return self.short_name


class User(AbstractUser):
    """
    Custom User
    """
    avatar = models.ImageField(upload_to='users/photos', verbose_name='Фото профиля', null=True, blank=True)

    def __str__(self):
        return self.username
