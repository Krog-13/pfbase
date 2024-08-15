from rest_framework import permissions
from django.contrib.auth.models import Group
from django.shortcuts import redirect


class IsCustomer(permissions.BasePermission):
    """
    Проверка на возможность редактирования
    """
    def has_permission(self, request, view):
        # print(dir(request))
        # print(request.authenticators)
        # print(dir(request.user))
        # print(request.user.groups)
        # print(request.user.get_group_permissions())
        # print(request.user.get_user_permissions())
        gp = Group.objects.get(name="customer")
        exist = request.user.groups.filter(name=gp)
        if exist:
            return True
        else:
            return False
