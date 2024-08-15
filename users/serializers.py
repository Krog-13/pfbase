from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from django.contrib.auth.password_validation import validate_password
from .models import User, Organization
# from documents.models import HistoryJournal
from django.contrib.auth.models import Permission
from django.contrib.auth import authenticate


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serialize for user profile
    """
    groups = serializers.SlugRelatedField(many=True, read_only=True, slug_field='name')

    class Meta:
        model = User
        fields = ("email", "user_status", "avatar",
                  "groups", "user_permissions")

    def __init__(self, *args, **kwargs): # by patch method username is not required ToDo: check it
        super(UserProfileSerializer, self).__init__(*args, **kwargs)
        if 'email' in self.fields and self.instance is not None:
            self.fields['email'].required = False


class UpdatePasswordSerializer(serializers.Serializer):
    ""
    old_password = serializers.CharField(
        write_only=True, required=True)
    new_password = serializers.CharField(
        write_only=True, required=True,
        validators=[validate_password])
    new_password2 = serializers.CharField(
        write_only=True, required=True)

    def validate(self, attrs):
        if attrs["new_password"] != attrs["new_password2"]:
            raise serializers.ValidationError(
                {"msg": "Password fields didn't match."})
        elif attrs["old_password"] == attrs["new_password"]:
            raise serializers.ValidationError(
                {"msg": "New password must be different from old password."})
        return attrs

    def save(self, obj, **kwargs):
        if not obj.check_password(self.validated_data['old_password']):
            raise serializers.ValidationError(
                {"msg": "Old password is incorrect"})
        obj.set_password(self.validated_data['new_password'])
        obj.save()
        return obj


class UserAVPSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("first_name", "last_name", "phone_number", "email")


class AuthTokenSerializer(serializers.Serializer):
    """
    Custom Serialize for auth token
    """
    email = serializers.EmailField()
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
        password = attrs.get('password')

        if email and password:
            user = authenticate(request=self.context.get('request'),
                                email=email, password=password)

            if not user:
                msg = 'Неверный email или пароль'
                raise serializers.ValidationError({"message": msg}, code='authorization')
        else:
            msg = 'Поле email и пароль обязательны для заполнения'
            raise serializers.ValidationError({"message": msg}, code='authorization')

        attrs['user'] = user
        return attrs

class UserSerializer(serializers.ModelSerializer):
    """
    Serialize for user
    """
    # avatar = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ("id", "email", "user_status", "avatar")

    # def get_avatar(self, obj):
    #     if obj.avatar and hasattr(obj.avatar, 'url'):
    #         return obj.avatar.url
    #     return None


class RegisterSerializer(serializers.ModelSerializer):
    """
    Serialize for registration
    """
    email = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all())]
    )
    password = serializers.CharField(
        write_only=True, required=True,
        validators=[validate_password])
    password_confirm = serializers.CharField(
        write_only=True, required=True)

    class Meta:
        model = User
        fields = ("password", "password_confirm", "email")

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError(
                {"message": "Пароли не совпадают"})
        return attrs

    def create(self, validated_data):
        user = User.objects.create(
            email=validated_data["email"],
        )
        user.set_password(validated_data["password"])
        user.is_active = False
        user.save()
        return user


class OrganizationSerializer(serializers.ModelSerializer):
    """
    Сериализатор для организаций
    """
    class Meta:
        model = Organization
        fields = ("short_name", "identifier", "address", "subsidiaries")


class EmailSerializer(serializers.Serializer):
    subject = serializers.CharField(max_length=164)
    message = serializers.CharField()
    notification_message = serializers.CharField()
    recipient_list = serializers.CharField()
    act_id = serializers.CharField(max_length=128)
    # recipient_list = serializers.ListField(child=serializers.EmailField())


class PermissionSerializer(serializers.ModelSerializer):
    """
    Serialize by user permissions
    """
    class Meta:
        model = Permission
        fields = ("id", "name", "codename")
