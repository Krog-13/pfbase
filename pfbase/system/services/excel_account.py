from zipfile import BadZipFile

from openpyxl import load_workbook
from openpyxl.utils.exceptions import InvalidFileException
from django.db import IntegrityError, transaction
from rest_framework.exceptions import ValidationError

from ..serializers.user import RegistrationUserSerializer


class ExcelAccount:
    def __init__(self, excel_file, request):
        self.dcm_code = "DCM_PRF"
        self.excel_file = excel_file
        self.request = request

    def make_workbook(self):
        try:
            workbook = load_workbook(self.excel_file, read_only=True, data_only=True)
        except (BadZipFile, InvalidFileException, OSError, ValueError) as error:
            raise ValidationError({'file': 'Upload a valid .xlsx file.'}) from error
        if 'account' not in workbook.sheetnames:
            raise ValidationError({'file': 'The workbook must contain an account sheet.'})
        return workbook

    def read_accounts(self):
        """Read only the account sheet as records without saving anything."""
        workbook = self.make_workbook()
        try:
            rows = workbook['account'].iter_rows(values_only=True)
            headers = next(rows)

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
        return users

    def create_profile(self, users):
        mutable_data["HSE_PRF_UID"] = user.id
        create_profile(mutable_data, request.user.id, user)

        author = User.objects.get(id=author_id)
        indicators = prepare_data_for_update(users)
        body = {
            "short_name": {"ru": f"Профиль {user.username}",
                           "kk": f"Профиль {user.username}",
                           "en": f"Profile {user.username}"},
            "code": user.id,
            "dictionary_id": Dictionaries.objects.getByCode("HSE_PRF"),
            "organization_id": user.organization.id if user.organization else None,
            "indicators": indicators}
        return ElementService().create_element_iv(author, body)

    def prepare_data_for_update(profile_data):
        indicators = []
        upper_keys = [key for key in profile_data if key == key.upper()]
        if not upper_keys:
            return indicators

        indicators_qs = DctIndicators.objects.filter(
            code__in=upper_keys,
            dictionary__code="HSE_PRF"
        )

        indicators_map = {ind.code: ind for ind in indicators_qs}

        for key in upper_keys:
            profile_ind = indicators_map.get(key)
            if not profile_ind:
                continue
            if getattr(profile_data, "getlist", None) and profile_ind.is_multiple:
                raw_value = profile_data.getlist(key)
            else:
                raw_value = profile_data.get(key)

            value = cast_value(raw_value, profile_ind.type_value, profile_ind.is_multiple)

            indicators.append({
                "code": key,
                "value": value,
                "type": profile_ind.type_value
            })
        return indicators

    def cast_single_value(value, type_value):
        if type_value in INT_TYPES:
            return int(value)

        if type_value in TYPE_CASTERS:
            return TYPE_CASTERS[type_value](value)

        if type_value == "bool":
            if isinstance(value, bool):
                return value
            return str(value).lower() in {"true", "1", "yes"}

        if type_value == "json":
            if isinstance(value, (dict, list)):
                return value
            return json.loads(value)

        return value

    def cast_value(value, type_value, is_multiple=False):
        INT_TYPES = {"int", "dct", "dcm", "user", "org", "list"}
        if value is None:
            return None
        try:
            if is_multiple:
                if not isinstance(value, (list, tuple)):
                    value = [value]
                return [
                    cast_single_value(v, type_value)
                    for v in value
                ]
            return cast_single_value(value, type_value)

        except (ValueError, TypeError, json.JSONDecodeError):
            return value
