from django.contrib.auth.models import Group, Permission
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from ..models.user import User
from ..security import audit, validate_access_rules


def validated_password(password, user):
    try:
        validate_password(password, user=user)
    except DjangoValidationError as error:
        raise serializers.ValidationError({'password': error.messages})


class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = '__all__'


class RolesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = '__all__'


class UserSerializer(serializers.ModelSerializer):
    account_status = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'last_login', 'is_superuser', 'username', 'first_name', 'last_name', 'email',
                  'is_staff', 'is_active', 'date_joined', 'avatar', 'organization', 'groups',
                  'expires_at', 'locked_until', 'block_reason', 'failed_login_attempts',
                  'password_changed_at', 'access_rules', 'account_status')
        read_only_fields = ('id', 'last_login', 'date_joined', 'failed_login_attempts',
                            'password_changed_at', 'account_status')

    def get_account_status(self, obj):
        if not obj.is_active:
            return 'disabled'
        if obj.expires_at and obj.expires_at <= timezone.now():
            return 'expired'
        if obj.locked_until and obj.locked_until > timezone.now():
            return 'locked'
        return 'active'

    def validate_access_rules(self, value):
        try:
            validate_access_rules(value)
        except DjangoValidationError as error:
            raise serializers.ValidationError(error.messages)
        return value

    def validate_email(self, value):
        query = User.objects.filter(email__iexact=value)
        if self.instance:
            query = query.exclude(pk=self.instance.pk)
        if value and query.exists():
            raise serializers.ValidationError('Email is already registered.')
        return value.lower()

    def validate(self, attrs):
        actor = self.context['request'].user
        security_fields = {'is_superuser', 'is_staff', 'is_active', 'groups', 'expires_at',
                           'locked_until', 'block_reason', 'access_rules', 'username', 'email'}
        if self.instance and self.instance.is_superuser and not actor.is_superuser:
            raise serializers.ValidationError('Only a superuser may manage a superuser account.')
        if security_fields.intersection(attrs) and not actor.has_perm('pfbase.manage_account_security'):
            raise serializers.ValidationError('Account security permission is required.')
        if 'is_superuser' in attrs and not actor.is_superuser:
            raise serializers.ValidationError('Only a superuser may assign superuser status.')
        return attrs

    @transaction.atomic
    def update(self, instance, validated_data):
        instance = User.objects.select_for_update().get(pk=instance.pk)
        if validated_data.get('locked_until', object()) is None:
            instance.failed_login_attempts = 0
            if 'block_reason' not in validated_data:
                validated_data['block_reason'] = ''
        user = super().update(instance, validated_data)
        audit('account_admin_updated', user, reason=','.join(sorted(validated_data)))
        return user


class RegistrationUserSerializer(UserSerializer):
    password = serializers.CharField(write_only=True, trim_whitespace=False)
    password_confirm = serializers.CharField(write_only=True, trim_whitespace=False)
    organization_id = serializers.IntegerField(required=False, allow_null=True)

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ('password', 'password_confirm', 'organization_id')
        extra_kwargs = {'email': {'required': True}, 'username': {'required': False}}

    def validate(self, attrs):
        if not attrs.get('username'):
            attrs['username'] = attrs.get('email', '').replace('@', '_').lower()
        if not attrs['username']:
            raise serializers.ValidationError('Username is required.')
        if User.objects.filter(username__iexact=attrs['username']).exists():
            raise serializers.ValidationError('Username is already registered.')
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError('Passwords do not match.')
        validated_password(attrs['password'], User(username=attrs['username'], email=attrs.get('email', ''),
                           first_name=attrs.get('first_name', ''), last_name=attrs.get('last_name', '')))
        return super().validate(attrs)

    @transaction.atomic
    def create(self, validated_data):
        password = validated_data.pop('password')
        validated_data.pop('password_confirm')
        groups = validated_data.pop('groups', [])
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        user.groups.set(groups)
        return user


class SetPasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(write_only=True, trim_whitespace=False)
    confirm_password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError('Passwords do not match.')
        validated_password(attrs['new_password'], self.instance)
        return attrs

    @transaction.atomic
    def save(self, obj, **kwargs):
        obj = User.objects.select_for_update().get(pk=obj.pk)
        validated_password(self.validated_data['new_password'], obj)
        obj.set_password(self.validated_data['new_password'])
        obj.save(update_fields=['password'])
        audit('password_admin_reset', obj)
        return obj


class ChangePasswordSerializer(SetPasswordSerializer):
    old_password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate(self, attrs):
        attrs = super().validate(attrs)
        if attrs['old_password'] == attrs['new_password']:
            raise serializers.ValidationError('New password must differ from the old password.')
        return attrs

    @transaction.atomic
    def save(self, obj, **kwargs):
        obj = User.objects.select_for_update().get(pk=obj.pk)
        if not obj.check_password(self.validated_data['old_password']):
            raise serializers.ValidationError('Old password is incorrect.')
        validated_password(self.validated_data['new_password'], obj)
        obj.set_password(self.validated_data['new_password'])
        obj.save(update_fields=['password'])
        return obj


class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True, trim_whitespace=False)
    confirm_password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError('Passwords do not match.')
        return attrs
