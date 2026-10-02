import uuid
import hashlib
from unittest.mock import patch
from datetime import timedelta
import concurrent.futures

from django.test import TestCase, TransactionTestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth.hashers import check_password

from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import User
from files.models import File, FileStatus
from sharing.models import ShareLink
from qr_codes.models import QRCode

from django.core.cache import cache

@override_settings(
    R2_ENDPOINT_URL='https://dummy.r2.cloudflarestorage.com',
    R2_ACCESS_KEY_ID='dummy',
    R2_SECRET_ACCESS_KEY='dummy',
    R2_BUCKET_NAME='dummy'
)
class SharingAPITests(TestCase):
    def setUp(self):
        cache.clear()
        self.client = APIClient()
        self.user = User.objects.create_user(email='test@example.com', password='password123')
        self.other_user = User.objects.create_user(email='other@example.com', password='password123')
        
        self.file = File.objects.create(
            owner=self.user,
            original_filename='test.png',
            storage_key='test_key.png',
            file_size=1024,
            content_type='image/png',
            status=FileStatus.ACTIVE
        )

    def test_create_share_link(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(reverse('sharelink-list'), {
            'file_id': str(self.file.id),
            'password': 'secretpassword',
            'max_downloads': 5
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('share_url', response.data)
        
        share_link = ShareLink.objects.get(id=response.data['id'])
        self.assertTrue(check_password('secretpassword', share_link.password_hash))
        self.assertEqual(share_link.max_downloads, 5)

    def test_revoke_share_link(self):
        self.client.force_authenticate(user=self.user)
        create_resp = self.client.post(reverse('sharelink-list'), {'file_id': str(self.file.id)})
        share_id = create_resp.data['id']

        revoke_url = reverse('sharelink-revoke', kwargs={'pk': share_id})
        self.client.post(revoke_url)

        share_link = ShareLink.objects.get(id=share_id)
        self.assertFalse(share_link.is_active)

    def test_public_resolve_get(self):
        self.client.force_authenticate(user=self.user)
        create_resp = self.client.post(reverse('sharelink-list'), {'file_id': str(self.file.id)})
        raw_token = create_resp.data['share_url'].split('/')[-1]

        self.client.logout()
        resolve_url = reverse('public-share-resolve-get', kwargs={'token': raw_token})
        response = self.client.get(resolve_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['filename'], 'test.png')
        self.assertFalse(response.data['password_required'])

    def test_public_resolve_expired(self):
        self.client.force_authenticate(user=self.user)
        create_resp = self.client.post(reverse('sharelink-list'), {
            'file_id': str(self.file.id),
            'expires_at': (timezone.now() - timedelta(days=1)).isoformat()
        })
        raw_token = create_resp.data['share_url'].split('/')[-1]

        self.client.logout()
        resolve_url = reverse('public-share-resolve-get', kwargs={'token': raw_token})
        response = self.client.get(resolve_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK) 

    def test_verify_password(self):
        self.client.force_authenticate(user=self.user)
        create_resp = self.client.post(reverse('sharelink-list'), {'file_id': str(self.file.id), 'password': 'mypassword'})
        raw_token = create_resp.data['share_url'].split('/')[-1]

        self.client.logout()
        verify_url = reverse('public-share-verify', kwargs={'token': raw_token})
        
        # Wrong password
        resp = self.client.post(verify_url, {'password': 'wrong'})
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        
        # Correct password
        resp = self.client.post(verify_url, {'password': 'mypassword'})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn(f'share_auth_{raw_token}', resp.cookies)
        
    def test_verify_password_rate_limiting(self):
        self.client.force_authenticate(user=self.user)
        create_resp = self.client.post(reverse('sharelink-list'), {'file_id': str(self.file.id), 'password': 'mypassword'})
        raw_token = create_resp.data['share_url'].split('/')[-1]
        self.client.logout()
        verify_url = reverse('public-share-verify', kwargs={'token': raw_token})
        
        # Hit it 5 times (allowed)
        for _ in range(5):
            resp = self.client.post(verify_url, {'password': 'wrong'})
            self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
            
        # 6th time should be throttled
        resp = self.client.post(verify_url, {'password': 'wrong'})
        self.assertEqual(resp.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    @patch('files.storage.StorageService.generate_download_url')
    def test_download_limits(self, mock_generate):
        mock_generate.return_value = "https://mock-download-url"
        self.client.force_authenticate(user=self.user)
        create_resp = self.client.post(reverse('sharelink-list'), {'file_id': str(self.file.id), 'max_downloads': 1})
        raw_token = create_resp.data['share_url'].split('/')[-1]

        self.client.logout()
        download_url = reverse('public-share-download', kwargs={'token': raw_token})
        
        resp1 = self.client.post(download_url)
        self.assertEqual(resp1.status_code, status.HTTP_200_OK)
        
        # Second should fail
        resp2 = self.client.post(download_url)
        self.assertEqual(resp2.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(resp2.data['error'], 'Download limit reached')

    def test_edit_share(self):
        self.client.force_authenticate(user=self.user)
        create_resp = self.client.post(reverse('sharelink-list'), {'file_id': str(self.file.id)})
        share_id = create_resp.data['id']
        
        self.client.patch(reverse('sharelink-detail', kwargs={'pk': share_id}), {
            'max_downloads': 10,
            'password': 'newpassword'
        })
        
        share_link = ShareLink.objects.get(id=share_id)
        self.assertEqual(share_link.max_downloads, 10)
        self.assertTrue(check_password('newpassword', share_link.password_hash))

    @patch('qr_codes.services.QRGeneratorService.generate_qr')
    def test_regenerate_token(self, mock_generate_qr):
        mock_generate_qr.return_value = "new_qr_key.png"
        self.client.force_authenticate(user=self.user)
        create_resp = self.client.post(reverse('sharelink-list'), {'file_id': str(self.file.id)})
        share_id = create_resp.data['id']
        old_raw_token = create_resp.data['share_url'].split('/')[-1]
        
        # Add a QR code
        QRCode.objects.create(share_link_id=share_id, storage_key="old_key.png")
        
        regen_resp = self.client.post(reverse('sharelink-regenerate-token', kwargs={'pk': share_id}))
        self.assertEqual(regen_resp.status_code, status.HTTP_200_OK)
        new_raw_token = regen_resp.data['share_url'].split('/')[-1]
        self.assertNotEqual(old_raw_token, new_raw_token)
        
        # Old token fails
        self.client.logout()
        resp_old = self.client.get(reverse('public-share-resolve-get', kwargs={'token': old_raw_token}))
        self.assertEqual(resp_old.status_code, status.HTTP_404_NOT_FOUND)
        
        resp_new = self.client.get(reverse('public-share-resolve-get', kwargs={'token': new_raw_token}))
        self.assertEqual(resp_new.status_code, status.HTTP_200_OK)


