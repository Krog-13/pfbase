from io import StringIO
import os
from unittest.mock import patch

from asgiref.sync import async_to_sync
from django.contrib.auth.models import Group, Permission
from django.core.management import call_command, CommandError
from django.db import IntegrityError, transaction
from django.test import Client, TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from .system.models.user import User
from .system.models.security import SecurityEvent
from .system.operator_role import IB_OPERATOR_GROUP, IB_OPERATOR_PERMISSIONS

PASSWORD = 'Operator!9-test-password'


class IBOperatorTests(TestCase):
    def setUp(self):
        self.output = StringIO()
        with patch.dict(os.environ, {'TEST_IB_PASSWORD': PASSWORD}):
            call_command('create_ib_operator', 'test_ib_operator', password_env='TEST_IB_PASSWORD', stdout=self.output)
        self.operator = User.objects.get(username='test_ib_operator')
        self.target = User.objects.create_user('ordinary', 'ordinary@example.test', PASSWORD)
        self.browser = Client()
        self.assertTrue(self.browser.login(username=self.operator.username, password=PASSWORD))

    def test_command_assigns_only_requested_permissions(self):
        self.assertTrue(self.operator.is_staff)
        self.assertFalse(self.operator.is_superuser)
        self.assertTrue(self.operator.is_ib_operator)
        self.assertEqual(self.operator.get_all_permissions(), IB_OPERATOR_PERMISSIONS)
        self.assertEqual(list(self.operator.groups.values_list('name', flat=True)), [IB_OPERATOR_GROUP])
        self.assertNotIn(PASSWORD, self.output.getvalue())

    def test_admin_index_contains_only_logs_and_add_user(self):
        response = self.browser.get('/admin/')
        self.assertEqual(response.status_code, 200)
        models = {model['object_name']: model for app in response.context['app_list'] for model in app['models']}
        self.assertEqual(set(models), {'User', 'SecurityEvent'})
        self.assertIn('add_url', models['User'])
        self.assertIsNone(models['User']['admin_url'])

    def test_operator_creates_ordinary_user_without_update_permission(self):
        url = reverse('admin:pfbase_user_add')
        form = self.browser.get(url)
        self.assertEqual(form.status_code, 200)
        self.assertNotContains(form, 'name="groups"')
        self.assertNotContains(form, 'name="is_staff"')
        response = self.browser.post(url, {'username': 'new_person', 'email': 'new@example.test',
            'first_name': 'New', 'last_name': 'Person', 'password1': PASSWORD, 'password2': PASSWORD, '_save': 'Save'})
        self.assertEqual(response.status_code, 302)
        created = User.objects.get(username='new_person')
        self.assertTrue(created.check_password(PASSWORD))
        self.assertFalse(created.is_staff or created.is_superuser or created.is_ib_operator)
        self.assertFalse(created.groups.exists() or created.user_permissions.exists())
        self.assertFalse(self.operator.has_perm('pfbase.change_user'))
        self.assertTrue(SecurityEvent.objects.filter(user=created, actor_id=self.operator.pk, event='account_created').exists())

    def test_operator_cannot_inject_privileges_during_creation(self):
        for name in ('is_staff', 'is_superuser', 'is_ib_operator', 'groups', 'user_permissions', 'access_rules'):
            response = self.browser.post(reverse('admin:pfbase_user_add'), {
                'username': 'injected', 'email': 'injected@example.test',
                'password1': PASSWORD, 'password2': PASSWORD, name: '1'})
            self.assertEqual(response.status_code, 403)
        self.assertFalse(User.objects.filter(username='injected').exists())

    def test_no_user_list_edit_delete_or_password_reset_even_by_url(self):
        for route in ('admin:pfbase_user_changelist', 'admin:pfbase_user_change',
                      'admin:pfbase_user_delete', 'admin:auth_user_password_change'):
            url = reverse(route, args=[] if route.endswith('changelist') else [self.target.pk])
            self.assertEqual(self.browser.get(url).status_code, 403)
            self.assertEqual(self.browser.post(url, {'username': 'changed', '_saveasnew': '1'}).status_code, 403)
        self.target.refresh_from_db()
        self.assertEqual(self.target.username, 'ordinary')
        self.assertTrue(self.target.check_password(PASSWORD))

    def test_security_events_are_read_only(self):
        event = SecurityEvent.objects.filter(user=self.target).first()
        self.assertEqual(self.browser.get(reverse('admin:pfbase_securityevent_changelist')).status_code, 200)
        detail = reverse('admin:pfbase_securityevent_change', args=[event.pk])
        self.assertEqual(self.browser.get(detail).status_code, 200)
        self.assertEqual(self.browser.post(detail, {'reason': 'tampered'}).status_code, 403)
        self.assertEqual(self.browser.post(reverse('admin:pfbase_securityevent_add'), {}).status_code, 403)
        self.assertEqual(self.browser.post(reverse('admin:pfbase_securityevent_delete', args=[event.pk]), {'post': 'yes'}).status_code, 403)
        event.refresh_from_db()
        self.assertNotEqual(event.reason, 'tampered')

    def test_extra_permissions_do_not_expand_operator_access(self):
        self.operator.user_permissions.set(Permission.objects.all())
        self.operator.refresh_from_db()
        self.assertEqual(self.operator.get_all_permissions(), IB_OPERATOR_PERMISSIONS)
        self.assertEqual(async_to_sync(self.operator.aget_all_permissions)(), IB_OPERATOR_PERMISSIONS)
        self.assertFalse(self.operator.has_perm('pfbase.change_user'))
        self.assertFalse(self.operator.has_perm('pfbase.change_organization'))
        self.assertTrue(self.browser.login(username=self.operator.username, password=PASSWORD))
        self.assertEqual(self.browser.get(reverse('admin:pfbase_organization_changelist')).status_code, 403)

    def test_jwt_and_session_cookie_cannot_access_api(self):
        api = APIClient()
        response = api.post('/api/token/', {'username': self.operator.username, 'password': PASSWORD}, format='json')
        self.assertEqual(response.status_code, 401)
        self.assertNotIn('access', response.data)
        self.assertEqual(self.browser.get('/api/stm/users/').status_code, 401)
        self.assertEqual(self.browser.get('/admin/').status_code, 200)

    def test_operator_flag_invalidates_older_api_tokens(self):
        api = APIClient()
        pair = api.post('/api/token/', {'username': self.target.username, 'password': PASSWORD}, format='json').data
        self.target.is_staff = self.target.is_ib_operator = True
        self.target.save(update_fields=['is_staff', 'is_ib_operator'])
        api.credentials(HTTP_AUTHORIZATION='Bearer ' + pair['access'])
        self.assertEqual(api.get('/api/stm/users/').status_code, 401)
        self.assertEqual(api.post('/api/token/refresh/', {'refresh': pair['refresh']}, format='json').status_code, 401)

    def test_superuser_admin_and_ordinary_api_still_work(self):
        user = User.objects.create_superuser('root_test', 'root@example.test', PASSWORD)
        browser = Client()
        self.assertTrue(browser.login(username=user.username, password=PASSWORD))
        self.assertEqual(browser.get(reverse('admin:pfbase_user_change', args=[self.target.pk])).status_code, 200)
        api = APIClient()
        response = api.post('/api/token/', {'username': self.target.username, 'password': PASSWORD}, format='json')
        self.assertEqual(response.status_code, 200)

    def test_db_forbids_operator_superuser_combination(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            User.objects.filter(pk=self.operator.pk).update(is_superuser=True)

    def test_command_does_not_overwrite_existing_account(self):
        with self.assertRaises(CommandError), patch.dict(os.environ, {'TEST_IB_PASSWORD': PASSWORD}):
            call_command('create_ib_operator', 'test_ib_operator', password_env='TEST_IB_PASSWORD', stdout=StringIO())
        self.assertEqual(User.objects.filter(username='test_ib_operator').count(), 1)
