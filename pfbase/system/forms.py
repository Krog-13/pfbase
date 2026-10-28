from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models.user import User


class OperatorUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name')

    def clean_username(self):
        value = self.cleaned_data['username']
        if User.objects.filter(username__iexact=value).exists():
            raise forms.ValidationError('Username is already registered.')
        return value

    def clean_email(self):
        value = self.cleaned_data['email'].lower()
        if User.objects.filter(email__iexact=value).exists():
            raise forms.ValidationError('Email is already registered.')
        return value
