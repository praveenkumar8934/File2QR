import uuid
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from accounts.models import User
from files.models import File, FileStatus
from sharing.models import ShareLink
from qr_codes.models import QRCode
from unittest.mock import patch
import hashlib

@override_settings(
    R2_ENDPOINT_URL='https://dummy.r2.cloudflarestorage.com',
    R2_ACCESS_KEY_ID='dummy',
    R2_SECRET_ACCESS_KEY='dummy',
    R2_BUCKET_NAME='dummy'
)
class QRCodeAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(email='test@example.com', password='password123')
        self.file = File.objects.create(
            owner=self.user,
            original_filename='test.png',
            storage_key='test_key.png',
            file_size=1024,
            content_type='image/png',
            status=FileStatus.ACTIVE
        )

        self.share_link = ShareLink.objects.create(
            file=self.file,
            owner=self.user,
            token_hash=hashlib.sha256(b"dummy_token").hexdigest()
        )

    @patch('requests.put')
    def test_generate_qr_code(self, mock_put):
        # mock put_object
        mock_put.return_value.status_code = 200

        self.client.force_authenticate(user=self.user)
        response = self.client.post(reverse('qrcode-list'), {
            'share_link_id': str(self.share_link.id),
            'raw_token': 'dummy_token'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(QRCode.objects.filter(share_link=self.share_link).exists())

    @patch('requests.put')
    def test_generate_qr_code_idempotent(self, mock_put):
        mock_put.return_value.status_code = 200

        self.client.force_authenticate(user=self.user)
        # Create first
        self.client.post(reverse('qrcode-list'), {
            'share_link_id': str(self.share_link.id),
            'raw_token': 'dummy_token'
        })
        # Try again
        response = self.client.post(reverse('qrcode-list'), {
            'share_link_id': str(self.share_link.id),
            'raw_token': 'dummy_token'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK) # not 201
        self.assertEqual(QRCode.objects.count(), 1)

    @patch('requests.put')
    @patch('files.storage.StorageService.generate_download_url')
    def test_download_qr_code(self, mock_generate, mock_put):
        mock_put.return_value.status_code = 200
        mock_generate.return_value = "https://qr-download-url"
        self.client.force_authenticate(user=self.user)
        
        # Create
        create_resp = self.client.post(reverse('qrcode-list'), {
            'share_link_id': str(self.share_link.id),
            'raw_token': 'dummy_token'
        })
        qr_id = create_resp.data['id']

        # Download
        download_url = reverse('qrcode-download', kwargs={'pk': qr_id})
        response = self.client.get(download_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['download_url'], "https://qr-download-url")
