from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from .system.models.listvalues import ListValues
from .system.models.organization import Organization
from .system.models.user import User


class CurrentUserTests(TestCase):
    def test_jwt_returns_the_signed_in_users_profile_and_groups(self):
        password = 'Current-user-test!9'
        user = User.objects.create_user(
            'member', 'member@example.test', password, first_name='Ivan', last_name='Petrov',
        )
        organization_type = ListValues.objects.create(list='organization_types', code='company', author=user)
        organization_name = {'en': 'Company', 'kk': 'Компания', 'ru': 'Компания'}
        organization = Organization.objects.create(code='HSE_KMG_INTER', full_name=organization_name,
                                                   type=organization_type)
        user.organization = organization
        user.save(update_fields=['organization'])
        assigned_group = Group.objects.create(name='lead')
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
            'email': 'member@example.test',
            'fio': 'Ivan Petrov',
            'user_id': user.pk,
            'organization': 'HSE_KMG_INTER',
            'organization_id': organization.pk,
            'organization_name': organization_name,
            'roles': ['lead'],
        })

        user.groups.clear()
        self.assertEqual(api.get(url).status_code, 401)
