from django.db import models
from django.contrib.auth.models import AbstractUser


class Organization(models.Model):
    """
    Организации
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
    User model
    """
    class Status(models.TextChoices):
        IN_SEARCH = 'S', 'Активно ищу работу'
        NOT_SEARCH = 'N', 'Не ищу работу'
        PASS_SEARCH = 'P', 'Рассматриваю предложения'

    username = models.CharField(
        "username",
        max_length=150,
        unique=False,
    )
    email = models.EmailField(unique=True, verbose_name='Почта')
    avatar = models.ImageField(upload_to='users/photos', verbose_name='Фото профиля', null=True, blank=True)
    user_status = models.CharField(max_length=1, choices=Status.choices, default=Status.IN_SEARCH,
                                   verbose_name='Статус поиска работы')

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email
