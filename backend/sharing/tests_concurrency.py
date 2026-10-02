import hashlib
import concurrent.futures
from unittest.mock import patch
from django.test import TransactionTestCase, override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import User
from files.models import File, FileStatus
from sharing.models import ShareLink
from django.db import connection

from django.core.cache import cache

@override_settings(
    R2_ENDPOINT_URL='https://dummy.r2.cloudflarestorage.com',
    R2_ACCESS_KEY_ID='dummy',
    R2_SECRET_ACCESS_KEY='dummy',
    R2_BUCKET_NAME='dummy',
    REST_FRAMEWORK={
        'DEFAULT_THROTTLE_CLASSES': [],
        'DEFAULT_AUTHENTICATION_CLASSES': (
            'accounts.authentication.JWTCookieAuthentication',
        ),
    } # Disable throttling so it doesn't interfere with concurrency tests
)
class PostgreSQLConcurrencyTests(TransactionTestCase):
    def setUp(self):
        cache.clear()
        # We ensure that this test is running against PostgreSQL to actually test select_for_update
        self.assertTrue('postgresql' in connection.vendor, "Concurrency test must be run with PostgreSQL to test select_for_update()")

        self.user = User.objects.create_user(email='concurrency@example.com', password='password123')
        self.file = File.objects.create(
            owner=self.user,
            original_filename='test.png',
            storage_key='test_key.png',
            file_size=1024,
            content_type='image/png',
            status=FileStatus.ACTIVE
        )

    def run_concurrent_downloads(self, max_downloads, concurrent_workers=20):
        raw_token = "concurrent_random_token"
        hashed = hashlib.sha256(raw_token.encode('utf-8')).hexdigest()
        
        share_link = ShareLink.objects.create(
            file=self.file,
            owner=self.user,
            token_hash=hashed,
            max_downloads=max_downloads
        )
        
        def download_attempt():
            from django.db import connection
            try:
                client = APIClient()
                url = reverse('public-share-download', kwargs={'token': raw_token})
                res = client.post(url)
                if res.status_code not in (200, 403):
                    print(f"Concurrency error status: {res.status_code}, {res.data}")
                return res.status_code
            finally:
                connection.close()

        with patch('files.storage.StorageService.generate_download_url', return_value="https://mock-download-url"):
            with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_workers) as executor:
                futures = [executor.submit(download_attempt) for _ in range(concurrent_workers)]
                results = [f.result() for f in futures]
                
        success_count = results.count(status.HTTP_200_OK)
        forbidden_count = results.count(status.HTTP_403_FORBIDDEN)
        
        share_link.refresh_from_db()
        return success_count, forbidden_count, share_link.download_count

    @patch('rest_framework.throttling.SimpleRateThrottle.allow_request', return_value=True)
    def test_max_downloads_one(self, mock_throttle):
        success, forbidden, db_count = self.run_concurrent_downloads(max_downloads=1, concurrent_workers=20)
        self.assertEqual(success, 1)
        self.assertEqual(forbidden, 19)
        self.assertEqual(db_count, 1)

    @patch('rest_framework.throttling.SimpleRateThrottle.allow_request', return_value=True)
    def test_max_downloads_five(self, mock_throttle):
        success, forbidden, db_count = self.run_concurrent_downloads(max_downloads=5, concurrent_workers=20)
        # In a real highly concurrent system with max_downloads=5, exactly 5 should succeed
        self.assertEqual(success, 5)
        self.assertEqual(forbidden, 15)
        self.assertEqual(db_count, 5)
