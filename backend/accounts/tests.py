from django.test import TestCase, override_settings
from django.conf import settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

User = get_user_model()

from django.core.cache import cache

class AuthenticationTests(TestCase):
    def setUp(self):
        cache.clear()
        self.client = APIClient()
        self.register_url = reverse('register')
        self.login_url = reverse('login')
        self.logout_url = reverse('logout')
        self.me_url = reverse('me')
        self.user_data = {
            'email': 'test@example.com',
            'password': 'StrongPassword123!',
            'first_name': 'Test',
            'last_name': 'User'
        }
        self.user = User.objects.create_user(**self.user_data)

    def test_register_success(self):
        data = {
            'email': 'newuser@example.com',
            'password': 'AnotherStrongPassword123!',
            'first_name': 'New',
            'last_name': 'User'
        }
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email='newuser@example.com').exists())

    def test_register_duplicate_email(self):
        response = self.client.post(self.register_url, self.user_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_invalid_email(self):
        data = self.user_data.copy()
        data['email'] = 'invalid-email'
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_weak_password(self):
        data = self.user_data.copy()
        data['email'] = 'weak@example.com'
        data['password'] = '123'
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_success(self):
        response = self.client.post(self.login_url, {
            'email': self.user_data['email'],
            'password': self.user_data['password']
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access_token', response.cookies)
        self.assertIn('refresh_token', response.cookies)

    def test_login_invalid(self):
        response = self.client.post(self.login_url, {
            'email': self.user_data['email'],
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertNotIn('access_token', response.cookies)

    def test_me_authenticated(self):
        # First login to set cookies
        self.client.post(self.login_url, {
            'email': self.user_data['email'],
            'password': self.user_data['password']
        })
        # Then get /me
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], self.user_data['email'])

    def test_me_unauthenticated(self):
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout(self):
        self.client.post(self.login_url, {
            'email': self.user_data['email'],
            'password': self.user_data['password']
        })
        response = self.client.post(self.logout_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.cookies['access_token'].value, '')
        self.assertEqual(response.cookies['refresh_token'].value, '')

    def test_logout_with_expired_or_invalid_token(self):
        # Even with an invalid token, logout should succeed and clear cookies (assuming CSRF is valid, though this test client bypasses CSRF)
        self.client.cookies['access_token'] = 'invalid_token'
        response = self.client.post(self.logout_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.cookies['access_token'].value, '')
        self.assertEqual(response.cookies['refresh_token'].value, '')

    def test_refresh_success(self):
        login_resp = self.client.post(self.login_url, {
            'email': self.user_data['email'],
            'password': self.user_data['password']
        })
        refresh_token = login_resp.cookies['refresh_token'].value
        
        self.client.cookies['refresh_token'] = refresh_token
        response = self.client.post(reverse('refresh'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access_token', response.cookies)

    def test_refresh_invalid(self):
        self.client.cookies['refresh_token'] = 'invalid_refresh_token'
        response = self.client.post(reverse('refresh'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

class CSRFTests(TestCase):
    def setUp(self):
        cache.clear()
        self.csrf_client = APIClient(enforce_csrf_checks=True)
        self.user = User.objects.create_user(
            email='csrftest@example.com',
            password='password123',
            first_name='CSRF',
            last_name='Test'
        )
        self.login_url = reverse('login')
        self.logout_url = reverse('logout')
        self.csrf_url = reverse('csrf')

    def test_authenticated_post_without_csrf_rejected(self):
        # Login to get cookies
        self.csrf_client.post(self.login_url, {'email': 'csrftest@example.com', 'password': 'password123'})
        
        # Try logout without CSRF token
        response = self.csrf_client.post(self.logout_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('CSRF Failed', str(response.data))

    def test_authenticated_post_with_valid_csrf_succeeds(self):
        # Login to get auth cookies
        self.csrf_client.post(self.login_url, {'email': 'csrftest@example.com', 'password': 'password123'})
        
        # Fetch CSRF token
        csrf_resp = self.csrf_client.get(self.csrf_url)
        csrf_token = csrf_resp.cookies['csrftoken'].value
        
        # Try logout with CSRF token header
        response = self.csrf_client.post(
            self.logout_url,
            HTTP_X_CSRFTOKEN=csrf_token
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Unauthenticated users sending POST to logout will be blocked by CSRF (403) before 401, because LogoutAuth checks CSRF.
        response = self.csrf_client.post(self.logout_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

