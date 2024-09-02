from .base_model import Enum
from django.contrib import admin


@admin.register(Enum)
class EnumAdmin(admin.ModelAdmin):
    """
    Abstract Documents in the admin panel
    """
    fields = (("list", "code"), ("short_name", "full_name"), "active", "author")
    list_display = ("get_name", "code", "id")
    search_fields = ('get_name', 'id')

    def get_name(self, obj):
        return obj.short_name["ru"]
