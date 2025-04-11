from django.contrib.auth.models import Group, Permission
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from django.contrib.auth.password_validation import validate_password
from ..models.user import User
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError


class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = '__all__'


class RolesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = '__all__'


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = 'id', 'last_login', 'is_superuser', 'username', 'first_name', 'last_name', 'email', \
            'is_staff', 'is_active', 'date_joined', 'avatar', 'organization', 'groups'


class RegistrationUserSerializer(serializers.ModelSerializer):
    """
    Сериализатор для регистрации пользователя
    """
    @staticmethod
    def unique_email_lowercase(value):
        lowercase_email = value.lower()
        if User.objects.filter(email__iexact=lowercase_email).exists():
            raise ValidationError("Этот email уже зарегистрирован.")
        return value

    username = serializers.CharField(min_length=4, max_length=40, required=False)

    email = serializers.EmailField(
        required=True,
        validators=[unique_email_lowercase]
    )
    password = serializers.CharField(
        write_only=True, required=True,
        validators=[validate_password]
    )
    password_confirm = serializers.CharField(
        write_only=True, required=True
    )
    first_name = serializers.CharField(min_length=2, max_length=50, required=False, default="fn")
    last_name = serializers.CharField(min_length=2, max_length=50, required=False, default="ln")
    groups = serializers.ListField(required=False)
    organization_id = serializers.IntegerField(required=False)
    avatar = serializers.ImageField(required=False)
    is_active = serializers.BooleanField(default=True)
    is_staff = serializers.BooleanField(default=False)

    class Meta:
        model = User
        fields = ("password", "password_confirm", "email", "username", "first_name", "last_name", "organization_id",
                  "groups", "avatar", "is_active", "is_staff")

    def validate(self, attrs):
        if not attrs.get("username"):
            local_part, domain = attrs["email"].split("@", 1)
            first_subdomain = domain.split(".", 1)[0]
            base_username = f"{local_part}_{first_subdomain}"
            attrs["username"] = base_username.lower() # set username by email
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError(
                {"message": "Пароли не совпадают"}
            )
        return attrs

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'].lower(),
            email=validated_data['email'].lower(),
            password=validated_data['password'],
            last_name=validated_data['last_name'],
            first_name=validated_data['first_name'],
            organization_id=validated_data.get('organization_id', None),
            is_active=validated_data['is_active'],
            is_staff=validated_data['is_staff'],
            avatar=validated_data.get('avatar', None))

        user.set_password(validated_data["password"])
        user.groups.set(validated_data.get('groups', []))
        user.save()
        return user




class AuthTokenSerializer(serializers.Serializer):
    """
    Custom Serialize for auth token
    """
    email = serializers.EmailField(required=False, allow_blank=True)
    username = serializers.CharField(required=False, allow_blank=True)
    password = serializers.CharField(
        style={'input_type': 'password'},
        trim_whitespace=False,
        write_only=True
    )
    token = serializers.CharField(
        label="Token",
        read_only=True
    )

    def validate(self, attrs):
        email = attrs.get('email')
        username = attrs.get('username')
        password = attrs.get('password')
        msg = 'Неверные учетные данные'

        if username and password:
            user = authenticate(request=self.context.get('request'),
                                username=username.lower(), password=password)
        elif email and password:
            try:
                current_user = User.objects.get(email__iexact=email)
                user = authenticate(request=self.context.get('request'),
                                    username=current_user.username, email=email, password=password)
                if not user:
                    msg = 'Пользователь с таким email не найден в системе'

            except User.DoesNotExist:
                user = authenticate(request=self.context.get('request'),
                                    email=email, password=password)
                if not user:
                    msg = 'Пользователь с таким email не найден в системе'
        else:
            msg = 'Данные для авторизации не указаны'
            raise serializers.ValidationError({"message": msg}, code='authorization')

        if not user:
            raise serializers.ValidationError({"message": msg}, code='authorization')

        attrs['user'] = user
        return attrs


class ChangePasswordSerializer(serializers.Serializer):
    """Custom update update"""
    old_password = serializers.CharField(
        write_only=True, required=True)
    new_password = serializers.CharField(
        write_only=True, required=True,
        validators=[validate_password])
    confirm_password = serializers.CharField(
        write_only=True, required=True)

    def validate(self, attrs):
        if attrs["new_password"] != attrs["confirm_password"]:
            raise serializers.ValidationError(
                {"message": "Password fields didn't match."})
        elif attrs["old_password"] == attrs["new_password"]:
            raise serializers.ValidationError(
                {"message": "New password must be different from old password."})
        return attrs

    def save(self, obj, **kwargs):
        if not obj.check_password(self.validated_data['old_password']):
            raise serializers.ValidationError(
                {"message": "Old password is incorrect"})
        obj.set_password(self.validated_data['new_password'])
        obj.save()
        return obj


# User password reset
class PasswordResetSerializer(serializers.Serializer):
    """Password reset with OTP JWT"""
    email = serializers.EmailField()

    def validate_email(self, value):
        try:
            self.user = User.objects.get(email=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("User email does not exist")
        return value

    def save(self, **kwargs):
        token_generator = PasswordResetTokenGenerator()
        token = token_generator.make_token(self.user)
        return self.user, token

class PasswordResetConfirmSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, data):
        if data["password"] != data["confirm_password"]:
            raise serializers.ValidationError("Password do not match")
        return data

    def save(self, user):
        user.set_password(self.validated_data["password"])
        user.save()
