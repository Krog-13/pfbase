from rest_framework.response import Response
from rest_framework import status
# from documents.models import DocumentField, FieldValue, User
# from documents.common import journal_create

# def get_user_ids(journal_id, code):
#     try:
#         indicator_id = DocumentField.objects.get(idc_code=code)
#     except DocumentField.DoesNotExist:
#         return Response({"Error msg": f"Code not found - {code}"}, status=status.HTTP_400_BAD_REQUEST)
#     return FieldValue.objects.filter(journal_document_id=journal_id, indicator_id=indicator_id.id)
#
#
# def get_user_emails(user_ids):
#     emails = []
#     for user_id in user_ids.split(","):
#         try:
#             user = User.objects.get(id=user_id)
#         except User.DoesNotExist:
#             continue
#         emails.append(user.email)
#     return emails
#
#
# def set_notification(recipient_list, message, user, act_id):
#     journal = {"document_id": 4,
#                "short_name": "Уведомление",
#                "doc_number": "1",
#                "doc_status": "created",
#                "history": False,
#                "parent_id": act_id}
#     indicator = [
#         {"code": "902", "value": message},
#         {"code": "908", "value": recipient_list}
#     ]
#     file, files = None, []
#     return journal_create(journal, indicator, user, file, files)

