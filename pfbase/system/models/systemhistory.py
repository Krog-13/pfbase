from django.db import models

# class Action(models.TextChoices):
#     CREATED = 'create', 'Create'
#     UPDATED = 'update', 'Update'
#     DELETED = 'delete', 'Delete'
#
# class SystemHistory(models.Model):
#     action = models.CharField(
#         max_length=10, choices=Action.choices, verbose_name='Действие', default=Action.CREATED)
#     stamp = models.JSONField(verbose_name='Слепок', null=True, blank=True)
#     author = models.ForeignKey(to="User", on_delete=models.CASCADE, verbose_name='Автор')
#     created_at = models.DateTimeField(auto_now_add=True, blank=True,
#                                       verbose_name='Дата и время действия')