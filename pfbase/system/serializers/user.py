from django.contrib.auth.models import Group
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from django.contrib.auth.password_validation import validate_password
from ..models.user import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = 'last_login', 'is_superuser', 'username', 'first_name', 'last_name', 'email', \
            'is_staff', 'is_active', 'date_joined', 'avatar', 'is_blocked', 'organization'


class RegisterUserSerializer(serializers.ModelSerializer):
    """
    Сериализатор для регистрации пользователей
    """
    username = serializers.CharField(min_length=6, max_length=20,
                                     validators=[UniqueValidator(queryset=User.objects.all())])

    email = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all())]
    )
    password = serializers.CharField(
        write_only=True, required=True,
        validators=[validate_password]
    )
    password_confirm = serializers.CharField(
        write_only=True, required=True
    )

    class Meta:
        model = User
        fields = ("password", "password_confirm", "email", "username")

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError(
                {"message": "Пароли не совпадают"}
            )
        return attrs

    def create(self, validated_data):
        user = User.objects.create(
            email=validated_data["email"],
        )
        user.set_password(validated_data["password"])
        user.is_active = False  # Пользователь должен подтвердить регистрацию
        user.save()
        return user


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = '__all__'

