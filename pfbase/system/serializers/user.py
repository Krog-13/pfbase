from rest_framework import serializers
from ..models.user import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = 'last_login', 'is_superuser', 'username', 'first_name', 'last_name', 'email', \
            'is_staff', 'is_active', 'date_joined', 'avatar', 'is_blocked', 'organization'
