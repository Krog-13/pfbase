from django.contrib.auth.models import Group
from .models.notification import Notification
from .models.listvalues import ListValues
from .models.organization import Organization
from .models.user import User
from django.contrib.auth.admin import UserAdmin, GroupAdmin as BaseGroupAdmin
from django.contrib import admin
from .models.security import SecurityEvent
from .forms import OperatorUserCreationForm
from django.core.exceptions import PermissionDenied


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
        ),
        (
            'Account security',
            {'fields': ('is_ib_operator', 'expires_at', 'locked_until', 'block_reason', 'access_rules',
                        'failed_login_attempts', 'password_changed_at')}
        )
    )
    exclude = ("password", )
    list_display = ('username', 'email', 'organization', 'id')
    list_filter = ("organization",)
    list_select_related = ("organization",)
    readonly_fields = ('last_login', 'date_joined', 'failed_login_attempts', 'password_changed_at')

    def has_add_permission(self, request):
        if request.user.is_ib_operator:
            return request.user.has_perm('pfbase.add_user')
        return super().has_add_permission(request) and request.user.has_perm('pfbase.manage_account_security')

    def get_fieldsets(self, request, obj=None):
        if request.user.is_ib_operator and obj is None:
            return ((None, {'fields': ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')}),)
        return super().get_fieldsets(request, obj)

    def get_form(self, request, obj=None, **kwargs):
        if request.user.is_ib_operator and obj is None:
            kwargs['form'] = OperatorUserCreationForm
        return super().get_form(request, obj, **kwargs)

    def _add_view(self, request, form_url='', extra_context=None):
        if request.user.is_ib_operator:
            # Bypass UserAdmin's add+change requirement only for a strictly
            # limited form; never grant change_user just to enable creation.
            forbidden = {'is_staff', 'is_superuser', 'is_ib_operator', 'is_active',
                         'groups', 'user_permissions', 'access_rules', 'locked_until',
                         'expires_at', 'usable_password', '_saveasnew'}
            if forbidden.intersection(request.POST):
                raise PermissionDenied('Only ordinary user accounts may be created.')
            return admin.ModelAdmin.add_view(self, request, form_url, extra_context)
        return super()._add_view(request, form_url, extra_context)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        if request.user.is_ib_operator:
            raise PermissionDenied('Updating existing users is not allowed.')
        return super().change_view(request, object_id, form_url, extra_context)

    def response_add(self, request, obj, post_url_continue=None):
        if request.user.is_ib_operator:
            return admin.ModelAdmin.response_add(self, request, obj, post_url_continue)
        return super().response_add(request, obj, post_url_continue)

    def has_change_permission(self, request, obj=None):
        return (super().has_change_permission(request, obj)
                and request.user.has_perm('pfbase.manage_account_security')
                and (obj is None or not obj.is_superuser or request.user.is_superuser))

    def has_delete_permission(self, request, obj=None):
        return self.has_change_permission(request, obj) and super().has_delete_permission(request, obj)

    def get_readonly_fields(self, request, obj=None):
        fields = super().get_readonly_fields(request, obj)
        return fields if request.user.is_superuser else (*fields, 'is_superuser', 'is_ib_operator')

    def save_model(self, request, obj, form, change):
        from .security import audit
        if request.user.is_ib_operator:
            if change:
                raise PermissionDenied('Updating existing users is not allowed.')
            obj.is_staff = obj.is_superuser = obj.is_ib_operator = False
            obj.is_active = True
        super().save_model(request, obj, form, change)
        audit('account_admin_updated', obj, reason=','.join(form.changed_data), request=request)

# admin.site.register(User, CustomUserAdmin)
class GroupAdmin(BaseGroupAdmin):
    list_display = ("name", "id",)
    ordering = ("id",)
    search_fields = ("id", "name")

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(SecurityEvent)
class SecurityEventAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'event', 'subject_id', 'actor_id', 'result', 'reason')
    list_filter = ('event', 'result')
    readonly_fields = ('created_at', 'user', 'subject_id', 'actor_id', 'event', 'result', 'reason', 'address')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

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
            app['models'].sort(key=lambda x: ordering.get(x['name'], 100))

    # Sort so pfbase app always will be at the first place
    app_list.sort(key=lambda x: 0 if x['app_label'] == 'pfbase' else 1)
    return app_list

# Override get_app_list method in AdminSite
admin.AdminSite.get_app_list = get_app_list
