from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from .system.models.user import User


class CurrentUserTests(TestCase):
    def test_jwt_returns_only_the_signed_in_users_groups(self):
        password = 'Current-user-test!9'
        user = User.objects.create_user('member', 'member@example.test', password)
        assigned_group = Group.objects.create(name='Editors')
        user.groups.add(assigned_group)
        Group.objects.create(name='Viewers')
        api = APIClient()
        url = reverse('current_user')

        self.assertEqual(api.get(url).status_code, 401)
        login = api.post(reverse('token_obtain_pair'), {
            'username': user.username, 'password': password,
        }, format='json')
        self.assertEqual(login.status_code, 200)
        api.credentials(HTTP_AUTHORIZATION='Bearer ' + login.data['access'])

        response = api.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {
            'id': user.pk,
            'username': user.username,
            'groups': [{'id': assigned_group.pk, 'name': assigned_group.name}],
        })

        user.groups.clear()
        self.assertEqual(api.get(url).status_code, 401)
