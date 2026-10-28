import logging
import re


class RedactAuthSecrets(logging.Filter):
    """Also redact reset-link secrets from Django's normal HTTP error logs."""
    reset_path = re.compile(r'(/password-reset-confirm/\d+/)[^/\s?\"\']+')
    bearer = re.compile(r'(?i)(Bearer\s+)[A-Za-z0-9._~+-]+')
    secret_keys = {'password', 'old_password', 'new_password', 'confirm_password',
                   'password_confirm', 'access', 'refresh', 'token', 'authorization'}

    def redact(self, value):
        if isinstance(value, str):
            return self.bearer.sub(r'\1[redacted]', self.reset_path.sub(r'\1[redacted]', value))
        if isinstance(value, dict):
            return {key: '[redacted]' if str(key).lower() in self.secret_keys else self.redact(item)
                    for key, item in value.items()}
        if isinstance(value, tuple):
            return tuple(self.redact(item) for item in value)
        return value

    def filter(self, record):
        record.msg = self.redact(record.msg)
        record.args = self.redact(record.args)
        return True
