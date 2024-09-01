from .models import Category, Indicator, IndicatorParameter, Element, ElementIndicatorValue
from rest_framework.response import Response
from django.conf import settings
from rest_framework import status
import pickle


# # def minio_client():
# #     client = Minio(
# #         endpoint=settings.MINIO_SERVER,
# #         access_key=settings.MINIO_ACCESS_KEY,
# #         secret_key=settings.MINIO_SECRET_KEY,
# #         secure=False)
# #     return client


# # minio = minio_client()


# def get_table(output_report):
#     report = Dictionary.objects.get(id=output_report)
#     group = GroupIndicatorDictionary.objects.filter(report_id=report.id)
#     indicators = DictionaryIndicator.objects.filter(group_id__in=group)

#     file_name = report.report_file.name
#     template_name = report.template_link
#     file_path_templates = os.path.join(
#         settings.BASE_DIR, file_name)

#     workbook = load_workbook(file_path_templates)
#     worksheet = workbook.active

#     for indicator in indicators:
#         cell = indicator.excel_cell
#         if cell:
#             try:
#                 indicator_value = IndicatorValue.objects.get(
#                     indicator=indicator.id, output_report_id=output_report.id
#                 )
#                 if not indicator_value:
#                     worksheet[cell] = 0
#                 else:
#                     worksheet[cell] = indicator_value.indicator_value
#             except IndicatorValue.DoesNotExist:
#                 pass

#     in_memory_file = io.BytesIO()
#     workbook.save(in_memory_file)
#     in_memory_file.seek(0)
#     response = HttpResponse(
#         content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
#     response['Content-Disposition'] = f"attachment; filename*=utf-8''{quote(template_name)}"
#     response.write(in_memory_file.getvalue())

#     return response


# def get_excel_data(excel_file, report_id):
#     workbook = load_workbook(excel_file)
#     worksheet = workbook.active
#     report = Report.objects.get(id=report_id)
#     group_indicators = report.groupindicator_set.all()

#     matched_indicators = []
#     for group_indicator in group_indicators:
#         indicators = group_indicator.indicator_set.all()
#         for indicator in indicators:
#             cell_value = indicator.excel_cell
#             if cell_value is not None:
#                 indicator_value = worksheet[cell_value]
#                 parameters = []
#                 matched_indicators.append({
#                     'id': indicator.id,
#                     'indicator_value': indicator_value.value,
#                     'type_value': indicator.type_value,
#                     'description': indicator.description,
#                     'parameters': parameters
#                 })

#     response_data = {
#         'indicators': matched_indicators
#     }

#     return Response(response_data)


# def get_download_file(report_id, is_instruction=False):
#     if not is_instruction:
#         file_name = Report.objects.get(id=report_id).report_file.name
#         file_path_templates = os.path.join(
#             settings.BASE_DIR, file_name)
#     else:
#         file_name = Report.objects.get(id=report_id).instruction_file.name
#         file_path_templates = os.path.join(
#             settings.BASE_DIR, file_name)

#     if os.path.exists(file_path_templates):
#         headers = {"Content-Type": "multipart/byteranges", "Access-Control-Expose-Headers": "Content-Disposition",
#                    "Content-Disposition": f"attachment; filename*=utf-8''{quote(file_name)}"}
#         return FileResponse(open(file_path_templates, 'rb'), as_attachment=True, headers=headers)
#     else:
#         return Response({"status": "Файл не найден"}, status=status.HTTP_404_NOT_FOUND)


# def save_file_minio(excel, file_id):
#     bute_io = io.BytesIO()
#     pickle.dump(excel.read(), bute_io)
#     bute_io.seek(0)
#     minio.put_object(settings.MINIO_BUCKET, file_id,
#                      bute_io, len(bute_io.getvalue()))


# def get_file_minio(file_id, filename):
#     data_object = minio.get_object(bucket_name=settings.MINIO_BUCKET,
#                                    object_name=file_id)
#     headers = {"Content-Type": "multipart/byteranges", "Access-Control-Expose-Headers": "Content-Disposition",
#                "Content-Disposition": f"attachment; filename*=utf-8''{quote(filename)}"}
#     return FileResponse(data_object, as_attachment=True, filename=filename, headers=headers)\


def indicator_value_create_old(new_data):
    values = []
    for item in new_data:
        values.append(
            ElementIndicatorValue(
                indicator_value=item.get("value"),
                output_dictionary_id=item.get("out_dictionary"),
                indicator_id=item.get("indicator_id"),
                primary_id=item.get("primary_id"),
                idc_row=item.get("row_id"))
        )
    ElementIndicatorValue.objects.bulk_create(values)
    return Response({}, status=status.HTTP_201_CREATED)


def element_create(element, indicator):
    elm = Element.objects.create(
        short_name=element["name"],
        code=element["code"],
        abc_dictionary_id=element["dictionary_id"],
        parent_id=element["parent_id"])
    values = []
    for item in indicator:
        values.append(
            ElementIndicatorValue(
                indicator_value=item.get("value"),
                element_id=elm.id,
                indicator_id=item.get("indicator_id")))
    ElementIndicatorValue.objects.bulk_create(values)
    return Response({}, status=status.HTTP_201_CREATED)
