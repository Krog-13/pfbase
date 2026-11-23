from zipfile import BadZipFile
from datetime import date, datetime, time
import json

from openpyxl import load_workbook
from openpyxl.utils.exceptions import InvalidFileException
from django.db import IntegrityError, transaction
from rest_framework.exceptions import ValidationError

from ..serializers.user import RegistrationUserSerializer
from ...dictionary.models import Dictionaries, DctIndicators
from ...dictionary.service import ElementService
from ...exception import WrongType
from django.core.exceptions import ObjectDoesNotExist


class ExcelAccount:
    def __init__(self, excel_file, request):
        self.dcm_code = "DCM_PRF"
        self.excel_file = excel_file
        self.request = request
        self.profile_data = {}

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
        for row_number, account in enumerate(accounts, start=2):
            if all(value is None or value == '' for value in account.values()):
                continue
            value = account['groups']
            account['groups'] = value.split(',')
            serializer = RegistrationUserSerializer(data=account, context={'request': self.request})
            try:
                serializer.is_valid(raise_exception=True)
                user = serializer.save()
            except ValidationError as error:
                raise ValidationError({'row': row_number, 'errors': error.detail}) from error
            except IntegrityError as error:
                raise ValidationError({'row': row_number, 'errors': 'An account with these attributes already exists.'}) from error
            users.append(user)
            self.create_profile(user, account)
        return users

    def create_profile(self, user, account):
        try:
            dictionary = Dictionaries.objects.get(code='HSE_PRF')
        except Dictionaries.DoesNotExist as error:
            raise ValidationError({'profile': 'HSE_PRF dictionary is not configured.'}) from error
        profiles = []
        account['HSE_PRF_UID'] = user.pk
        try:
            body = {
                'short_name': {'ru': f'Профиль {user.username}',
                               'kk': f'Профиль {user.username}',
                               'en': f'Profile {user.username}'},
                'code': str(user.pk),
                'dictionary_id': dictionary.pk,
                'organization_id': user.organization_id,
                'indicators': self.prepare_data(account),
            }
            profiles.append(ElementService().create_element_iv(self.request.user, body))
        except ValidationError as error:
            raise ValidationError({'row': 1, 'errors': error.detail}) from error
        except (ObjectDoesNotExist, WrongType, ValueError, TypeError, IntegrityError) as error:
            raise ValidationError({'row': 1, 'profile': 'Invalid profile data.'}) from error
        return profiles

    def prepare_data(self, account):
        indicators = DctIndicators.objects.filter(
            dictionary__code='HSE_PRF',
            code__in=account.keys())
        result = []
        for indicator in indicators:
            value = account[indicator.code]
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
