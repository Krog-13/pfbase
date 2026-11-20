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
            print(account)
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
        return []
