from zipfile import BadZipFile
from datetime import date, datetime, time
import json
from functools import cached_property

from openpyxl import load_workbook
from openpyxl.utils.exceptions import InvalidFileException
from django.db import IntegrityError, transaction
from django.db.models.functions import Lower
from rest_framework.exceptions import ValidationError

from ..serializers.user import RegistrationUserSerializer
from ..models.user import User
from ...dictionary.models import Dictionaries, DctIndicators, Elements, ElementIndicatorValues
from ...dictionary.service import ElementService


class ExcelAccount:
    def __init__(self, excel_file, request):
        self.dcm_code = "DCM_PRF"
        self.excel_file = excel_file
        self.request = request
        self.profile_data = {}
        self.skipped_count = 0

    def make_workbook(self):
        try:
            workbook = load_workbook(self.excel_file, read_only=True, data_only=True)
        except (BadZipFile, InvalidFileException, OSError, ValueError) as error:
            raise ValidationError({'file': 'Upload a valid .xlsx file.'}) from error
        if 'account' not in workbook.sheetnames:
            workbook.close()
            raise ValidationError({'file': 'The workbook must contain an account sheet.'})
        return workbook

    def read_accounts(self):
        """Read only the account sheet as records without saving anything."""
        workbook = self.make_workbook()
        try:
            rows = workbook['account'].iter_rows(values_only=True)
            headers = next(rows, ())

            accounts = []
            for row_number, row in enumerate(rows, start=2):
                accounts.append(dict(zip(headers, row)))
            return accounts
        finally:
            workbook.close()

    @transaction.atomic
    def create_account(self, accounts):
        users = []
        profile_rows = []
        self.skipped_count = 0
        emails = {str(account.get('email') or '').strip().lower() for account in accounts}
        emails.discard('')
        existing_emails = set(User.objects.annotate(import_email=Lower('email')).filter(
            import_email__in=emails).values_list('import_email', flat=True)) if emails else set()
        for row_number, account in enumerate(accounts, start=2):
            if all(value is None or value == '' for value in account.values()):
                continue
            email = str(account.get('email') or '').strip().lower()
            if email and email in existing_emails:
                self.skipped_count += 1
                continue
            data = {key: value for key, value in account.items() if value is not None}
            if isinstance(data.get('email'), str):
                data['email'] = data['email'].strip()
            value = data.get('groups')
            if isinstance(value, str):
                data['groups'] = [group.strip() for group in value.split(',') if group.strip()]
            elif value is not None and not isinstance(value, (list, tuple)):
                data['groups'] = [value]
            if 'organization_id' in data:
                organization_id = data.pop('organization_id')
                if 'organization' in data and data['organization'] != organization_id:
                    raise ValidationError({'row': row_number, 'organization_id': 'Conflicting organizations.'})
                data['organization'] = organization_id
            serializer = RegistrationUserSerializer(data=data, context={'request': self.request})
            try:
                serializer.is_valid(raise_exception=True)
                user = serializer.save()
            except ValidationError as error:
                # The email may have been registered since the initial query.
                if (email and isinstance(error.detail, dict) and 'email' in error.detail
                        and User.objects.filter(email__iexact=email).exists()):
                    existing_emails.add(email)
                    self.skipped_count += 1
                    continue
                raise ValidationError({'row': row_number, 'errors': error.detail}) from error
            except IntegrityError as error:
                raise ValidationError({'row': row_number, 'errors': 'An account with these attributes already exists.'}) from error
            users.append(user)
            if email:
                existing_emails.add(email)
            profile_rows.append((row_number, user, account))
        self.create_profiles(profile_rows)
        return users

    @cached_property
    def profile_dictionary(self):
        try:
            return Dictionaries.objects.get(code='HSE_PRF')
        except Dictionaries.DoesNotExist as error:
            raise ValidationError({'profile': 'HSE_PRF dictionary is not configured.'}) from error

    @cached_property
    def profile_indicators(self):
        return {indicator.code: indicator for indicator in
                DctIndicators.objects.filter(dictionary_id=self.profile_dictionary.pk)}

    def create_profile(self, user, account):
        return self.create_profiles([(1, user, account)])

    @transaction.atomic
    def create_profiles(self, rows):
        """Insert profiles and their values in batches after ordinary registration."""
        if not rows:
            return []
        dictionary = self.profile_dictionary
        indicators = self.profile_indicators
        profiles = []
        prepared_rows = []
        for row_number, user, account in rows:
            profile_data = {**account, 'HSE_PRF_UID': user.pk}
            try:
                prepared = self.prepare_data(profile_data)
            except ValidationError as error:
                raise ValidationError({'row': row_number, 'errors': error.detail}) from error
            profiles.append(Elements(
                short_name={'ru': f'Профиль {user.username}',
                            'kk': f'Профиль {user.username}',
                            'en': f'Profile {user.username}'},
                code=str(user.pk), dictionary_id=dictionary.pk,
                organization_id=user.organization_id, author=self.request.user,
            ))
            prepared_rows.append((row_number, prepared))

        # Reuse the service's type-to-column mapping without its per-value queries.
        service = ElementService()
        values = []
        for profile, (row_number, prepared) in zip(profiles, prepared_rows):
            for item in prepared:
                indicator = indicators[item['code']]
                value = ElementIndicatorValues(element=profile, indicator=indicator)
                setter = service.separate_multiple_value if indicator.is_multiple else service.separate_value
                try:
                    valid = setter(value, indicator.type_value, item['value'])
                except (ValueError, TypeError) as error:
                    raise ValidationError({'row': row_number, indicator.code: 'Invalid indicator value.'}) from error
                if not valid:
                    raise ValidationError({'row': row_number, indicator.code: 'Unsupported indicator value.'})
                values.append(value)
        try:
            Elements.objects.bulk_create(profiles, batch_size=500)
            # PostgreSQL fills profile PKs; update the FK on the unsaved values.
            for value in values:
                value.element_id = value.element.pk
            ElementIndicatorValues.objects.bulk_create(values, batch_size=1000)
        except IntegrityError as error:
            raise ValidationError({'profile': 'Invalid profile data; import rolled back.'}) from error
        return profiles

    def prepare_data(self, account):
        result = []
        for indicator in self.profile_indicators.values():
            if indicator.code not in account:
                continue
            value = account[indicator.code]
            if value is None or value == '':
                continue
            try:
                if indicator.is_multiple:
                    if isinstance(value, str):
                        value = (json.loads(value) if value.strip().startswith('[') else
                                 [item.strip() for item in value.split(',') if item.strip()])
                    if not isinstance(value, (list, tuple)):
                        value = [value]
                    value = [self.cast_indicator_value(item, indicator.type_value) for item in value]
                else:
                    value = self.cast_indicator_value(value, indicator.type_value)
            except (ValueError, TypeError) as error:
                raise ValidationError({indicator.code: 'Invalid indicator value.'}) from error
            result.append({'code': indicator.code, 'value': value, 'type': indicator.type_value})
        return result

    @staticmethod
    def cast_indicator_value(value, type_value):
        if type_value in {'str', 'text', 'file'}:
            return str(value)
        if type_value in {'int', 'dct', 'dcm', 'list', 'user', 'org'}:
            if isinstance(value, float) and not value.is_integer():
                raise ValueError('Expected an integer.')
            return int(value)
        if type_value == 'float':
            return float(value)
        if type_value == 'bool':
            if str(value).strip().lower() in {'true', '1', 'yes'}:
                return True
            if str(value).strip().lower() in {'false', '0', 'no'}:
                return False
            raise ValueError('Expected a boolean.')
        if type_value == 'json' and isinstance(value, str):
            return json.loads(value)
        if type_value in {'date', 'datetime', 'time'} and isinstance(value, (date, datetime, time)):
            return value.strftime({'date': '%Y-%m-%d', 'datetime': '%Y-%m-%d %H:%M',
                                   'time': '%H:%M'}[type_value])
        return value
