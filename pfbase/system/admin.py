from django.contrib.auth.models import Group
from .models.notification import Notification
from .models.listvalues import ListValues
from .models.organization import Organization
from .models.user import User
from django.contrib.auth.admin import UserAdmin, GroupAdmin as BaseGroupAdmin
from django.contrib import admin


# Admin for System
@admin.register(ListValues)
class LVAdmin(admin.ModelAdmin):
    """
    List Value in admin panel
    """
    fields = ("list", "code", ("short_name", "full_name"), "author", "index_sort", "active")
    exclude = ("deleted_at",)
    list_display = ('list', 'code', 'get_name', 'id')
    list_filter = ("list", )
    list_per_page = 50

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
    fields = (("title", "message"), ("type_notification", "is_read"), ("receiver_user", "sender_user"))
    list_display = ('type_notification', 'sender_user', 'receiver_user', 'id')
    readonly_fields = ("record", "element")
    list_per_page = 50


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    """
    Organization in admin panel
    """
    fields = (("short_name", "full_name"), "code", "identifier", "index_sort", "type", "parent", "active")
    exclude = ("deleted_at",)
    list_display = ('get_name', 'get_full_name', 'identifier', 'id')

    def get_name(self, obj):
        return obj.short_name.get("ru", obj.code)

    def get_full_name(self, obj):
        return obj.full_name.get("ru", obj.code)


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """
    User in admin panel
    """
    fieldsets = (
        (
            "Main Section",
            {"fields": (("username", "email"), ("first_name", "last_name"), "organization")}
        ),
        (
            "Groups & Permissions",
            {"fields": ("groups", "user_permissions")}
        ),
        (
            "Other Section",
            {"fields": (("last_login", "date_joined"), "is_superuser", "is_staff", "is_active")}
        )
    )
    exclude = ("password", )
    list_display = ('username', 'email', 'organization', 'id')
    list_filter = ("organization",)
    list_select_related = ("organization",)

# admin.site.register(User, CustomUserAdmin)
class GroupAdmin(BaseGroupAdmin):
    list_display = ("name", "id",)
    ordering = ("id",)
    search_fields = ("id", "name")

admin.site.unregister(Group)
admin.site.register(Group, GroupAdmin)


def get_app_list(self, request, app_label=None):
    """
    Return a sorted list of all the installed apps that have been
    registered in this site.
    """
    sort_apps = ['pfbase'] # add new app name for sorting if needed
    ordering = {  # add new model name if new app in sort_apps was added
        "DCM Documents": 1,
        "DCM Indicators": 2,
        "DCM Document Records": 3,
        "DCM Indicator Values": 4,
        "DCM Record Histories": 5,
        "DCT Dictionaries": 6,
        "DCT Indicators": 7,
        "DCT Elements": 8,
        "DCT Indicator Values": 9,
        "DCT Element Histories": 10,
        "STM List Values": 11,
        "STM Notifications": 12,
        "STM Organizations": 13,
        "STM Users": 14,
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
