import uuid
from datetime import timedelta
from unittest import mock
from django.utils import timezone
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from django.core.management import call_command

from files.models import File, FileStatus
from sharing.models import ShareLink
from qr_codes.models import QRCode
from analytics.models import ShareEvent
from analytics.services import record_share_event, generate_qr_signature, verify_qr_signature, hash_ip

User = get_user_model()

@override_settings(
    ANALYTICS_IP_SALT='test-salt',
    QR_ANALYTICS_SIGNING_SECRET='test-qr-secret',
    CACHES={'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}} # Allow testing rate limits easily, wait no, user said: "Confirm production configuration does NOT silently use LocMemCache." but for tests it's okay, or I can use the default cache. Let's just use whatever is configured for tests. Actually, I won't override CACHES, I'll let it use what's configured, but I need to clear the cache before rate limit tests.
)
class AnalyticsTests(TestCase):
    def setUp(self):
        from django.core.cache import cache
        cache.clear()
        self.client = APIClient()
        self.user1 = User.objects.create_user(email='user1@test.com', password='password1')
        self.user2 = User.objects.create_user(email='user2@test.com', password='password2')
        
        self.file1 = File.objects.create(owner=self.user1, original_filename='test1.txt', file_size=100, status=FileStatus.ACTIVE)
        self.share1 = ShareLink.objects.create(file=self.file1, owner=self.user1, token_hash='hash1')
        # We need a real raw_token to hit resolve endpoint properly. 
        # The view uses token_hash from hash_token(raw_token).
        from sharing.views import hash_token
        self.raw_token = 'my-token'
        self.share1.token_hash = hash_token(self.raw_token)
        self.share1.save()

        self.qr1 = QRCode.objects.create(share_link=self.share1, storage_key='test-key')

    def test_event_generation_and_privacy(self):
        # 1. Privacy Claim: Raw IP addresses are never stored in analytics events. A salted one-way SHA-256 hash is used for privacy-preserving approximate unique-visitor measurement.
        request = mock.Mock()
        request.META = {'REMOTE_ADDR': '192.168.1.1'}
        request.headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        
        event = record_share_event(self.share1, ShareEvent.EventType.VIEW, request, success=True)
        
        self.assertIsNotNone(event)
        self.assertEqual(event.event_type, ShareEvent.EventType.VIEW)
        self.assertEqual(event.ip_hash, hash_ip('192.168.1.1'))
        # Ensure it's 64 chars (SHA-256 hex)
        self.assertEqual(len(event.ip_hash), 64)
        
        # Test API response doesn't leak ip_hash
        self.client.force_authenticate(user=self.user1)
        resp = self.client.get(reverse('analytics-share-detail', kwargs={'pk': self.share1.id}))
        self.assertEqual(resp.status_code, 200)
        self.assertNotIn('ip_hash', resp.data)
        
    def test_qr_security_and_semantics(self):
        # A valid normal share URL -> VIEW only
        url = reverse('public-share-resolve-get', kwargs={'token': self.raw_token})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        
        self.assertEqual(ShareEvent.objects.count(), 1)
        self.assertEqual(ShareEvent.objects.first().event_type, ShareEvent.EventType.VIEW)
        
        ShareEvent.objects.all().delete()
        
        # A valid QR URL -> VIEW + QR_SCAN
        sig = generate_qr_signature(str(self.qr1.id), self.raw_token)
        resp = self.client.get(f"{url}?qr={self.qr1.id}&sig={sig}")
        self.assertEqual(resp.status_code, 200)
        
        self.assertEqual(ShareEvent.objects.count(), 2)
        event_types = set(ShareEvent.objects.values_list('event_type', flat=True))
        self.assertIn(ShareEvent.EventType.VIEW, event_types)
        self.assertIn(ShareEvent.EventType.QR_SCAN, event_types)
        
        ShareEvent.objects.all().delete()
        
        # Modified signature -> no QR_SCAN
        resp = self.client.get(f"{url}?qr={self.qr1.id}&sig=badsig")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(ShareEvent.objects.count(), 1)
        self.assertEqual(ShareEvent.objects.first().event_type, ShareEvent.EventType.VIEW)
        
        ShareEvent.objects.all().delete()
        
        # Modified qr_id -> no QR_SCAN
        other_qr_id = uuid.uuid4()
        resp = self.client.get(f"{url}?qr={other_qr_id}&sig={sig}")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(ShareEvent.objects.count(), 1)
        self.assertEqual(ShareEvent.objects.first().event_type, ShareEvent.EventType.VIEW)
        
        ShareEvent.objects.all().delete()
        
        # Arbitrary params -> no QR_SCAN
        resp = self.client.get(f"{url}?qr=abc&sig=123")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(ShareEvent.objects.count(), 1)
        self.assertEqual(ShareEvent.objects.first().event_type, ShareEvent.EventType.VIEW)
        
        ShareEvent.objects.all().delete()
        
        # Inactive QR -> no QR_SCAN
        self.qr1.is_active = False
        self.qr1.save()
        from django.core.cache import cache
        cache.clear()
        resp = self.client.get(f"{url}?qr={self.qr1.id}&sig={sig}")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(ShareEvent.objects.count(), 1)
        self.assertEqual(ShareEvent.objects.first().event_type, ShareEvent.EventType.VIEW)
        
    def test_owner_authorization(self):
        ShareEvent.objects.create(
            share_link=self.share1,
            file=self.file1,
            event_type=ShareEvent.EventType.VIEW,
            ip_hash='test'
        )
        
        # User A -> User A analytics = allowed
        self.client.force_authenticate(user=self.user1)
        resp = self.client.get(reverse('analytics-share-detail', kwargs={'pk': self.share1.id}))
        self.assertEqual(resp.status_code, 200)
        
        # User B -> User A share analytics = rejected
        self.client.force_authenticate(user=self.user2)
        resp = self.client.get(reverse('analytics-share-detail', kwargs={'pk': self.share1.id}))
        self.assertEqual(resp.status_code, 404)
        
        # User B -> User A QR analytics = rejected
        resp = self.client.get(reverse('analytics-qr-detail', kwargs={'pk': self.qr1.id}))
        self.assertEqual(resp.status_code, 404)
        
        # Unauthenticated user -> analytics = rejected
        self.client.logout()
        resp = self.client.get(reverse('analytics-overview'))
        self.assertEqual(resp.status_code, 401)
        
    def test_analytics_rate_limiting(self):
        from django.core.cache import cache
        cache.clear()
        
        self.client.force_authenticate(user=self.user1)
        url = reverse('analytics-overview')
        
        # Assuming rate limit is 100/min for users (or whatever is configured for 'analytics' scope)
        # We will fire 101 requests
        for i in range(100):
            resp = self.client.get(url)
            if resp.status_code == 429:
                break
        
        # If it didn't break early, the 101st request should definitely be 429
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    def test_date_filters(self):
        now = timezone.now()
        # Event 1: Today
        ShareEvent.objects.create(share_link=self.share1, file=self.file1, event_type=ShareEvent.EventType.VIEW, ip_hash='1', created_at=now)
        # Event 2: 40 days ago
        old_event = ShareEvent.objects.create(share_link=self.share1, file=self.file1, event_type=ShareEvent.EventType.VIEW, ip_hash='2')
        old_event.created_at = now - timedelta(days=40)
        old_event.save()
        
        self.client.force_authenticate(user=self.user1)
        
        # Default (last 30 days) -> only 1 event
        resp = self.client.get(reverse('analytics-overview'))
        self.assertEqual(resp.data['total_views'], 1)
        
        # Custom range (last 60 days) -> 2 events
        from_str = (now - timedelta(days=60)).strftime('%Y-%m-%d')
        resp = self.client.get(f"{reverse('analytics-overview')}?from={from_str}")
        self.assertEqual(resp.data['total_views'], 2)
        
        # Ensure max 90 days is enforced
        far_past = (now - timedelta(days=100)).strftime('%Y-%m-%d')
        resp = self.client.get(f"{reverse('analytics-overview')}?from={far_past}")
        # The range is truncated to 90 days. Since we have events at 0 and 40, they are within 90 days.
        # But if we had an event at 95 days, it would be excluded.
        really_old_event = ShareEvent.objects.create(share_link=self.share1, file=self.file1, event_type=ShareEvent.EventType.VIEW, ip_hash='3')
        really_old_event.created_at = now - timedelta(days=95)
        really_old_event.save()
        
        resp = self.client.get(f"{reverse('analytics-overview')}?from={far_past}")
        self.assertEqual(resp.data['total_views'], 2) # the 95-day event is excluded
        
    def test_retention_command(self):
        now = timezone.now()
        old = ShareEvent.objects.create(share_link=self.share1, file=self.file1, event_type=ShareEvent.EventType.VIEW, ip_hash='1')
        old.created_at = now - timedelta(days=95)
        old.save()
        
        recent = ShareEvent.objects.create(share_link=self.share1, file=self.file1, event_type=ShareEvent.EventType.VIEW, ip_hash='2')
        recent.created_at = now - timedelta(days=10)
        recent.save()
        
        self.assertEqual(ShareEvent.objects.count(), 2)
        
        call_command('cleanup_analytics')
        
        self.assertEqual(ShareEvent.objects.count(), 1)
        self.assertEqual(ShareEvent.objects.first().id, recent.id)
