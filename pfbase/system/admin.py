from .models.notification import Notification
from .models.listvalues import ListValues
from .models.organization import Organization
from .models.user import User
from django.contrib.auth.admin import UserAdmin
from django.contrib import admin


# Admin for System
@admin.register(ListValues)
class LVAdmin(admin.ModelAdmin):
    """
    List Value in admin panel
    """
    list_display = ('list', 'code', 'get_name', 'id')
    list_filter = ("list", )

    def get_name(self, obj):
        return obj.short_name.get("ru", obj.code)

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.author = request.user
        super().save_model(request, obj, form, change)


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """
    Notification in admin panel
    """
    list_display = ('type_notification', 'sender_user', 'receiver_user', 'id')


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    """
    Organization in admin panel
    """
    list_display = ('get_name', 'get_full_name', 'identifier', 'id')

    def get_name(self, obj):
        return obj.short_name.get("ru", obj.code)

    def get_full_name(self, obj):
        return obj.full_name.get("ru", obj.code)


@admin.register(User)
class CustomUserAdmin(admin.ModelAdmin):
    """
    User in admin panel
    """
    # fieldsets = (("username", "email"), ("id", "first_name"))
    list_display = ('username', 'email', 'organization', 'id')
    list_filter = ("organization",)
    list_select_related = ("organization",)

# admin.site.register(User, CustomUserAdmin)


def get_app_list(self, request, app_label=None):
    """
    Return a sorted list of all the installed apps that have been
    registered in this site.
    """
    sort_apps = ['pfbase'] # add new app name for sorting if needed
    ordering = {  # add new model name if new app in sort_apps was added
        "DCM Документы": 1,
        "DCM Индикаторы": 2,
        "DCM Записи документов": 3,
        "DCM Значения индикаторов": 4,
        "DCM Истории записей": 5,
        "DCT Справочники": 6,
        "DCT Индикаторы": 7,
        "DCT Элементы": 8,
        "DCT Значения индикаторов": 9,
        "DCT История элементов": 10,
        "STM Списки значений": 11,
        "STM Уведомления": 12,
        "STM Организации": 13,
        "STM Пользователи": 14,
    }
    app_dict = self._build_app_dict(request, app_label)
    app_list = sorted(app_dict.values(), key=lambda x: x['name'].lower())

    for app in app_list:
        if app['app_label'] in sort_apps:
            app['models'].sort(key=lambda x: ordering[x['name']])

    # Sort so pfbase app always will be at the first place
    app_list.sort(key=lambda x: 0 if x['app_label'] == 'pfbase' else 1)
    return app_list

# Override get_app_list method in AdminSite
admin.AdminSite.get_app_list = get_app_list
