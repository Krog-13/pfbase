from django.contrib import admin

from users.models import User, Organization


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    """
    Организации в админ панели
    """
    list_display = ('short_name', 'identifier', 'address', 'id')
    search_fields = ('short_name', 'identifier', 'address', 'id')


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """
    Пользователи в админ панели
    """
    list_display = ('email', 'username', 'id')
    search_fields = ('username', 'email', 'id')
