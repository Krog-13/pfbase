from django.core.exceptions import ValidationError


class PasswordComplexityValidator:
    def validate(self, password, user=None):
        if not (any(c.islower() for c in password) and any(c.isupper() for c in password)
                and any(c.isdigit() for c in password) and any(not c.isalnum() and not c.isspace() for c in password)):
            raise ValidationError(self.get_help_text(), code='password_complexity')

    def get_help_text(self):
        return 'Password must contain lowercase and uppercase letters, a digit and a non-space special character.'
