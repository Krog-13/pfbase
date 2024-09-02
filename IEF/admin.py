from .base_model import Enum
from django.contrib import admin


@admin.register(Enum)
class EnumAdmin(admin.ModelAdmin):
    """
    Abstract Documents in the admin panel
    """
    fields = (("list", "code"), ("short_name", "full_name"), "active")
    list_display = ("get_name", "code", "id")
    search_fields = ('get_name', 'id')

    def get_name(self, obj):
        return obj.list

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.author = request.user
        super().save_model(request, obj, form, change)
