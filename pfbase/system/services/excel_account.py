from zipfile import BadZipFile

from openpyxl import load_workbook
from openpyxl.utils.exceptions import InvalidFileException
from rest_framework.exceptions import ValidationError


class ExcelAccount:
    def __init__(self, excel_file):
        self.dcm_code = "DCM_PRF"
        self.excel_file = excel_file

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

    def create_account(self, accounts):

        pass

