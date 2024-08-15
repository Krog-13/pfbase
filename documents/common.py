from django.utils import timezone
from rest_framework.response import Response
from rest_framework import status
from .models import FieldValue, JournalDocument, DocumentField, HistoryJournal, ABCDocument
from django.db import IntegrityError, transaction
import logging.config
import re
from itertools import groupby
from documents.serializers import JournalDetailSerializer
from IEF.minio_client import MinioClient
from uuid import uuid4
from datetime import date, datetime

# init logging
logger = logging.getLogger("ief_logger")

minio = MinioClient()
minio.get_client()


def save_file_minio(files):
    files_naming = []
    if isinstance(files, list):
        for file in files:
            file_id = uuid4().hex
            file_data = f"{file.name},{file_id}"
            files_naming.append(file_data)
            minio.save_file_minio(file, file_id)
    else:
        file_id = uuid4().hex
        file_data = f"{files.name},{file_id}"
        files_naming.append(file_data)
        minio.save_file_minio(files, file_id)
    return files_naming


@transaction.atomic
def journal_create(journal_data, user, files_meta=None):
    journal = journal_data.get("journal")
    indicators = journal_data.get("indicator")

    try:
        abc_document = ABCDocument.objects.get(abc_code=journal["abc_code"])
    except ABCDocument.DoesNotExist:
        return Response({"Error msg": f"Code not found - {journal['abc_code']}"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        elm = JournalDocument.objects.create(
            short_name="Random Name",
            date_time=timezone.now(),
            abc_document=abc_document,
            parent_id=journal.get("parent_id"),
            author=user)
    except IntegrityError:
        return Response({"Msg": "duplicate key value violates unique constraint short_name"},
                        status=status.HTTP_400_BAD_REQUEST)
    values = []
    for item in indicators:
        pk = item.get("code")
        try:
            indicator = DocumentField.objects.get(idc_code=pk)
        except DocumentField.DoesNotExist:
            return Response({"Error msg": f"Code not found - {pk}"}, status=status.HTTP_400_BAD_REQUEST)
        if item.get("type") == "file":
            file = files_meta.get(item.get("code"))
            item["value"] = file
        values.append(
            FieldValue(
                indicator_value=item.get("value"),
                journal_document_id=elm.id,
                indicator_id=indicator.id))
    FieldValue.objects.bulk_create(values)
    if journal.get("history", True):
        HistoryJournal.objects.create(
            journal_status="created",
            author=user,
            stage="point",
            journal_document_id=elm.id)
    return Response({"journal_id": elm.id}, status=status.HTTP_201_CREATED)


def get_file_object(data, upload_files):
    result = []
    file_keys = [(i["code"], i["value"]) for i in data.get("indicator") if i["type"] == "file"]
    if file_keys:
        for key in file_keys:
            file = upload_files.get(key[1])
            if file:
                result.append((key[0], file))
        # file = upload_files.getlist(file_key)  # for multiple files
    return result


def get_file_object_super(data, upload_files):
    file_key = [i["value"] for i in data.get("indicator") if i["type"] == "file"]
    if file_key:
        file_key = file_key[0]
        if file_key.isdigit():
            file = upload_files[int(file_key)]
            return file


def journal_vac_update(journal_data, user):
    pass


@transaction.atomic
def journal_vac_create(journal_data, user):
    journal = journal_data.get("journal")
    indicators = journal_data.get("indicator")

    try:
        abc_document = ABCDocument.objects.get(abc_code=journal["abc_code"])
    except ABCDocument.DoesNotExist:
        return Response({"Error msg": f"Code not found - {journal['abc_code']}"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        elm = JournalDocument.objects.create(
            short_name="Random Name",
            date_time=timezone.now(),
            abc_document=abc_document,
            parent_id=journal.get("parent_id"),
            author=user)
    except IntegrityError:
        return Response({"Msg": "duplicate key value violates unique constraint short_name"},
                        status=status.HTTP_400_BAD_REQUEST)
    values = []
    for item in indicators:
        pk = item.get("code")
        try:
            indicator = DocumentField.objects.get(idc_code=pk)
        except DocumentField.DoesNotExist:
            return Response({"Error msg": f"Code not found - {pk}"}, status=status.HTTP_400_BAD_REQUEST)
        values.append(
            FieldValue(
                indicator_value=item.get("value"),
                journal_document_id=elm.id,
                indicator_id=indicator.id))
    FieldValue.objects.bulk_create(values)
    if journal.get("history", True):
        HistoryJournal.objects.create(
            journal_status="created",
            author=user,
            stage="point",
            journal_document_id=elm.id)
    return Response({"journal_id": elm.id}, status=status.HTTP_201_CREATED)


def journal_history_create(journal, author, stamp):
    if stamp:
        try:
            obj = JournalDocument.everything.get(id=journal.get("journal_document_id"))
        except JournalDocument.DoesNotExist:
            return Response({"Msg": "Journal document does not exist"},
                     status=status.HTTP_400_BAD_REQUEST)
        serializer = JournalDetailSerializer(obj)
        current_stamp = serializer.data
    else:
        current_stamp = None

    journal_document_id = journal.get("journal_document_id")
    signature = journal.get("signature", None)
    stage = journal.get("stage", None)
    # approval = DocumentField.objects.get(idc_code=204, indicator_doc__journal_document_id=journal_document_id)
    # averment = DocumentField.objects.get(idc_code=205, indicator_doc__journal_document_id=journal_document_id)

    approval = FieldValue.objects.get(journal_document_id=journal_document_id, indicator__idc_code=204)
    averment = FieldValue.objects.get(journal_document_id=journal_document_id, indicator__idc_code=205)
    approval2 = FieldValue.objects.filter(journal_document_id=journal_document_id, indicator__idc_code=206).first()
    averment2 = FieldValue.objects.filter(journal_document_id=journal_document_id, indicator__idc_code=207).first()

    HistoryJournal.objects.create(
        journal_status=journal.get("journal_status"),
        status_comment=journal.get("status_comment"),
        journal_document_id=journal_document_id,
        author=author,
        stage=stage,
        signature=signature,
        data_stamp=current_stamp)

    # send_approve_users()
    ids1 = approval.indicator_value.split(',')
    ids2 = averment.indicator_value.split(',')
    if approval2 and averment2:
        ids3 = approval2.indicator_value.split(',')
        ids4 = averment2.indicator_value.split(',')
    else:
        ids3, ids4 = [], []
    journal_status = "None"
    user_id = str(author.id)
    if user_id in ids1:
        ids = ids1
        journal_status = "averment"
    elif user_id in ids2:
        ids = ids2
        journal_status = "averment_abp"
    elif user_id in ids3:
        ids = ids3
        journal_status = "averment_root"
    elif user_id in ids4:
        ids = ids4
        journal_status = "signed"
    else:
        ids = []

    users = []
    queryset = HistoryJournal.objects.filter(stage="point").last()

    for user_id in ids:
        sign = HistoryJournal.objects.filter(author=user_id, journal_document_id=journal_document_id,
                                           signature=True, id__gt=queryset.id).last()
        if sign:
            users.append(sign)
    if len(users) == len(ids) and users:
            HistoryJournal.objects.create(
                journal_status=journal_status,
                status_comment=journal.get("status_comment"),
                journal_document_id=journal.get("journal_document_id"),
                author=author,
                signature=None,
                data_stamp=current_stamp)

    return Response({"Msg": "Journal History Created"},
                    status=status.HTTP_201_CREATED)


def indicator_create(journal_id, indicators):
    values = []
    for item in indicators:
        idc_code = item.get("code")
        try:
            indicator_id = DocumentField.objects.get(idc_code=idc_code)
        except DocumentField.DoesNotExist:
            return Response({"Error msg": f"Code not found - {idc_code}"}, status=status.HTTP_400_BAD_REQUEST)
        values.append(
            FieldValue(
                indicator_value=item.get("value"),
                journal_document_id=journal_id,
                indicator_id=indicator_id.id))
    FieldValue.objects.bulk_create(values)

    return Response({}, status=status.HTTP_201_CREATED)


@transaction.atomic
def journal_update(journal_data, user, file_meta=None):
    """Update journal"""
    journal = journal_data.get("journal")
    indicators = journal_data.get("indicator")
    objs = []
    try:
        journal_obj = JournalDocument.objects.get(abc_document__abc_code=journal.get("abc_code"), author=user)
    except JournalDocument.DoesNotExist:
        return Response({"Msg": "Journal act does not exist"},
                     status=status.HTTP_400_BAD_REQUEST)
    journal_obj.save()
    for item in indicators:
        _FV = FieldValue.objects.get(id=item.get("id"))
        _FV.indicator_value = item.get("value")
        objs.append(_FV)
    FieldValue.objects.bulk_update(objs, ["indicator_value"])
    return Response({"journal_id": journal_obj.id}, status=status.HTTP_200_OK)


def indicator_update(journal_id, indicators):
    """Update journal"""

    for item in indicators:
        try:
            indicator_id = DocumentField.objects.get(idc_code=item.get("code"))
        except DocumentField.DoesNotExist:
            return Response({"Error msg": f"Code not found - {item.get('code')}"}, status=status.HTTP_400_BAD_REQUEST)
        FieldValue.objects.update_or_create(indicator_id=indicator_id, journal_document_id=journal_id,
                                            defaults={"indicator_value": item.get("value"),
                                                      "indicator_id": indicator_id.id,
                                                      "journal_document_id": journal_id})
    return Response({"journal_id": journal_id}, status=status.HTTP_200_OK)


def upload_file(journal_id, string_path_file, code):
    try:
        indicator_id = DocumentField.objects.get(idc_code=code)
    except DocumentField.DoesNotExist:
        return Response({"Error msg": f"Code not found - {code}"}, status=status.HTTP_400_BAD_REQUEST)
    for file_data in string_path_file.split(";"):
        FieldValue.objects.create(indicator_value=file_data,
                journal_document_id=journal_id,
                indicator_id=indicator_id.id)
    return Response({}, status=status.HTTP_201_CREATED)


def update_file(field_id, string_path_file):
    try:
        field_value = FieldValue.objects.get(id=field_id)
    except FieldValue.DoesNotExist:
        return Response({"message": f"File not found by id - {field_id}"}, status=status.HTTP_400_BAD_REQUEST)
    for file_data in string_path_file.split(";"):
        field_value.indicator_value = file_data
        field_value.save()
    return Response({"message": "File update success!"}, status=status.HTTP_200_OK)


@transaction.atomic
def journal_createOLD(journal, indicators, user, string_path_file, file_order):
    try:
        elm = JournalDocument.objects.create(
            short_name=journal["short_name"],
            doc_number=journal["doc_number"],
            date_time=timezone.now(),
            abc_document_id=journal["document_id"],
            parent_id=journal.get("parent_id"),
            author=user)
    except IntegrityError:
        return Response({"Msg": "duplicate key value violates unique constraint short_name"},
                        status=status.HTTP_400_BAD_REQUEST)
    values = []
    for item in indicators:
        idc_code = item.get("code")
        try:
            indicator_id = DocumentField.objects.get(idc_code=idc_code)
        except DocumentField.DoesNotExist:
            return Response({"Error msg": f"Code not found - {idc_code}"}, status=status.HTTP_400_BAD_REQUEST)

        if item.get("type") == "calc":
            value = calculate_indicator(indicators, item["indicator_id"])
            if not value:
                transaction.set_rollback(True)
                return Response({"msg": "formula incorrect"}, status=status.HTTP_400_BAD_REQUEST)
            item["value"] = value
        elif item.get("type") == "files":
            for file_data in string_path_file.split(";"):
                FieldValue.objects.create(indicator_value=file_data,
                                          journal_document_id=elm.id,
                                          indicator_id=indicator_id.id)
            # item["value"] = string_path_file
            continue
        elif item.get("type") == "file":
            item["value"] = file_order

        values.append(
            FieldValue(
                indicator_value=item.get("value"),
                journal_document_id=elm.id,
                indicator_id=indicator_id.id))
    # values.append(FieldValue(indicator_value=3, journal_document_id=elm.id, indicator_id=6))  # default customer
    FieldValue.objects.bulk_create(values)
    if journal.get("history", True):
        HistoryJournal.objects.create(
            journal_status=journal["doc_status"],
            author=user,
            stage="point",
            journal_document_id=elm.id)
    return Response({"journal_id": elm.id}, status=status.HTTP_201_CREATED)


def calculate_indicator(indicators, indicator_id):
    """Calculation custom formula"""
    calc_indicator = DocumentField.objects.get(id=indicator_id)
    custom_rule = calc_indicator.custom_rule
    formula = custom_rule.get("calc")
    for idc in indicators:
        formula = formula.replace(f"{{{idc['indicator_id']}}}", str(idc["value"]))
    try:
        result = eval(formula)
    except (SyntaxError, NameError):
        logger.error("Syntax error formula incorrect")
        return False
    return round(result, 3)


def formula_values(start_range, end_range,  formula_output_report, additional_values=[]):
    """
    Получения значения показателей
    """
    try:
        indicators = FieldValue.objects.filter(indicator__id__range=(
            start_range, end_range), output_document_id=formula_output_report)
    except Exception as e:
        logger.error(f"Formula incorrect, check does it exist indicator id by range {start_range}-{end_range}")
        return ("Ошибка в формуле показателя")
    indicators_values = [float(indicator.indicator_value)
                         for indicator in indicators]
    if additional_values:
        indicators_values.extend(additional_values)
    return indicators_values


def get_range(part, formula_output_report):
    """
    Диапазон значении
    """
    range_start, range_end = map(int, part[1].split(':'))
    additional_values = []
    if part[2] is not None:
        additional_indicators = re.findall(r'\d+', part[2])
        try:
            for value_id in additional_indicators:
                indicator_value = FieldValue.objects.get(
                    indicator__id=value_id, output_document=formula_output_report).indicator_value
                additional_values.append(float(indicator_value))
        except FieldValue.DoesNotExist:
            logger.error(f"Formula incorrect")
            return ("Ошибка в формуле показателя")
    return [range_start, range_end, additional_values]


def calculate_formula(rule, formula_output_report):
    """
    Формула расчета
    """
    def calculate_average(start_range, end_range, additional_values=[]):
        indicators_values = formula_values(
            start_range, end_range, formula_output_report, additional_values)
        average = (sum(indicators_values)/len(indicators_values))
        return "{:.2f}".format(average)

    def calculate_max(start_range, end_range, additional_values=[]):
        indicators_values = formula_values(
            start_range, end_range, formula_output_report, additional_values)
        return max(indicators_values)

    def calculate_min(start_range, end_range, additional_values=[]):
        indicators_values = formula_values(
            start_range, end_range, formula_output_report, additional_values)
        return min(indicators_values)

    def calculate_sum(start_range, end_range, additional_values=[]):
        indicators_values = formula_values(
            start_range, end_range, formula_output_report, additional_values)
        return sum(indicators_values)

    parts = re.findall(
        r'(AVG|MAX|MIN|SUM)\((?:\{(\d+:\d+)\}((?:;\{\d+\})*)\))|([+*/-])|\{(\d+)\}|(\d+)', rule.get("calc"))

    modified_parts = []
    if parts:
        for part in parts:
            if part[0] == 'AVG':
                range_start, range_end, additional_values = get_range(
                    part, formula_output_report)
                avg_value = calculate_average(
                    range_start, range_end, additional_values)
                modified_parts.append(str(avg_value))
            elif part[0] == 'MAX':
                range_start, range_end, additional_values = get_range(
                    part, formula_output_report)
                max_value = calculate_max(
                    range_start, range_end, additional_values)
                modified_parts.append(str(max_value))
            elif part[0] == 'MIN':
                range_start, range_end, additional_values = get_range(
                    part, formula_output_report)
                min_value = calculate_min(
                    range_start, range_end, additional_values)
                modified_parts.append(str(min_value))
            elif part[0] == 'SUM':
                range_start, range_end, additional_values = get_range(
                    part, formula_output_report)
                sum_value = calculate_sum(
                    range_start, range_end, additional_values)
                modified_parts.append(str(sum_value))
            elif part[4]:
                value_id = int(part[4])
                indicator_value = FieldValue.objects.get(
                    indicator__id=value_id, output_document=formula_output_report)
                modified_parts.append(str(indicator_value))
            elif part[5]:
                modified_parts.append(part[5])
            elif part[3]:
                modified_parts.append(part[3])
            else:
                return "Неверная формула или значения показателей"
    else:
        return "Неверная формула или значения показателей"

    updated_formula = ''.join(modified_parts)
    return eval(updated_formula)


def download_file(value_id):
    """
    Download file from minIO
    """
    try:
        file_name = FieldValue.objects.get(id=value_id).indicator_value
    except FieldValue.DoesNotExist:
        return Response({"Message": "file not found"}, status=status.HTTP_404_NOT_FOUND)
    file = file_name.split(',')
    if file:
        return minio.get_file_minio(file[1], file[0])  # file[1] - file_id, file[0] - file_name
    return Response({"Message": "file not found"}, status=status.HTTP_404_NOT_FOUND)


def get_documents_id(data, status):
    current_date = date.today()
    result = []
    # data.sort(key=lambda x: x['journal_document_id'])

    # Then, use groupby to group the data
    # grouped_data = {k: list(v) for k, v in groupby(data, key=lambda x: x['journal_document_id'])}

    # print(grouped_data)
    data_set = []
    for item in data:
        data_set.append(item)
    data_set.sort(key=lambda x: x['journal_document_id'])
    result = {"active": [], "inactive": []}
    # Then, use groupby to group the data
    grouped_data = {k: list(v) for k, v in groupby(data, key=lambda x: x['journal_document_id'])}
    for key, value in grouped_data.items():
        # for item in value:
        date_one = datetime.strptime(value[0]["indicator_value"], '%Y-%m-%d').date()
        date_two = datetime.strptime(value[1]["indicator_value"], '%Y-%m-%d').date()
        if value[0]["indicator__idc_code"] == '102':
            if date_one <= current_date and date_two >= current_date:
                result["active"].append(key)
            else:
                result["inactive"].append(key)
        elif value[0]["indicator__idc_code"] == '103':
            if date_one <= current_date and date_two >= current_date:
                result["active"].append(key)
            else:
                result["inactive"].append(key)
    return result
