import uuid
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from django.conf import settings
from .models import File, FileStatus
from botocore.exceptions import ClientError

User = get_user_model()

class FileUploadTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='test@example.com', password='password123')
        self.other_user = User.objects.create_user(email='other@example.com', password='password123')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.upload_url = reverse('upload_url')

    @patch('files.storage.boto3.client')
    def test_upload_url_success(self, mock_boto):
        mock_client = MagicMock()
        mock_client.generate_presigned_url.return_value = "https://mock-url.com/upload"
        mock_boto.return_value = mock_client

        data = {
            'filename': 'photo.jpg',
            'content_type': 'image/jpeg',
            'file_size': 1024 * 1024  # 1MB
        }
        response = self.client.post(self.upload_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('upload_url', response.data)
        self.assertIn('file_id', response.data)
        
        file_record = File.objects.get(id=response.data['file_id'])
        self.assertEqual(file_record.status, FileStatus.UPLOADING)
        self.assertEqual(file_record.original_filename, 'photo.jpg')

    def test_upload_url_invalid_type(self):
        data = {
            'filename': 'script.sh',
            'content_type': 'application/x-sh',
            'file_size': 1024
        }
        response = self.client.post(self.upload_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('not allowed', response.data['error'])

    def test_upload_url_oversized(self):
        data = {
            'filename': 'large.mp4',
            'content_type': 'video/mp4',
            'file_size': settings.MAX_FILE_SIZE + 1024
        }
        response = self.client.post(self.upload_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('exceeds maximum', response.data['error'])

    @patch('files.storage.boto3.client')
    def test_confirm_upload_success(self, mock_boto):
        mock_client = MagicMock()
        mock_client.head_object.return_value = {
            'ContentLength': 1024 * 1024,
            'ContentType': 'image/jpeg'
        }
        mock_boto.return_value = mock_client

        # Create PENDING file
        file_record = File.objects.create(
            owner=self.user,
            original_filename='photo.jpg',
            storage_key='users/1/mock.jpg',
            file_size=1024 * 1024,
            content_type='image/jpeg',
            status=FileStatus.UPLOADING
        )

        confirm_url = reverse('confirm_upload', kwargs={'pk': file_record.id})
        response = self.client.post(confirm_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        file_record.refresh_from_db()
        self.assertEqual(file_record.status, FileStatus.ACTIVE)
        self.assertIsNotNone(file_record.uploaded_at)

    @patch('files.storage.boto3.client')
    def test_confirm_upload_wrong_user(self, mock_boto):
        # Create file owned by other_user
        file_record = File.objects.create(
            owner=self.other_user,
            original_filename='photo.jpg',
            storage_key='users/2/mock.jpg',
            file_size=1024 * 1024,
            content_type='image/jpeg',
            status=FileStatus.UPLOADING
        )

        confirm_url = reverse('confirm_upload', kwargs={'pk': file_record.id})
        response = self.client.post(confirm_url)
        # Should be 404 because get_object_or_404 filters by owner=request.user
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch('files.storage.boto3.client')
    def test_file_delete(self, mock_boto):
        mock_client = MagicMock()
        mock_boto.return_value = mock_client

        file_record = File.objects.create(
            owner=self.user,
            original_filename='photo.jpg',
            storage_key='users/1/mock.jpg',
            file_size=1024,
            content_type='image/jpeg',
            status=FileStatus.ACTIVE
        )

        delete_url = reverse('file_detail', kwargs={'pk': file_record.id})
        response = self.client.delete(delete_url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        file_record.refresh_from_db()
        self.assertEqual(file_record.status, FileStatus.DELETED)

    def test_file_list_excludes_deleted(self):
        File.objects.create(
            owner=self.user, original_filename='active.jpg', storage_key='1',
            file_size=100, content_type='image/jpeg', status=FileStatus.ACTIVE
        )
        File.objects.create(
            owner=self.user, original_filename='deleted.jpg', storage_key='2',
            file_size=100, content_type='image/jpeg', status=FileStatus.DELETED
        )

        response = self.client.get(reverse('file_list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['original_filename'], 'active.jpg')
