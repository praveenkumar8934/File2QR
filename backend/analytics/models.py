import uuid
from django.db import models
from sharing.models import ShareLink
from files.models import File
from qr_codes.models import QRCode

class ShareEvent(models.Model):
    class EventType(models.TextChoices):
        VIEW = 'VIEW', 'View'
        DOWNLOAD = 'DOWNLOAD', 'Download'
        QR_SCAN = 'QR_SCAN', 'QR Scan'
        PASSWORD_SUCCESS = 'PASSWORD_SUCCESS', 'Password Success'
        PASSWORD_FAILED = 'PASSWORD_FAILED', 'Password Failed'
        EXPIRED = 'EXPIRED', 'Expired'
        REVOKED = 'REVOKED', 'Revoked'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    share_link = models.ForeignKey(ShareLink, on_delete=models.CASCADE, related_name='events')
    file = models.ForeignKey(File, on_delete=models.CASCADE, related_name='events')
    qr_code = models.ForeignKey(QRCode, null=True, blank=True, on_delete=models.SET_NULL, related_name='events')
    
    event_type = models.CharField(max_length=20, choices=EventType.choices)
    created_at = models.DateTimeField(auto_now_add=True)
    
    ip_hash = models.CharField(max_length=64, null=True, blank=True)
    device_type = models.CharField(max_length=50, null=True, blank=True)
    browser = models.CharField(max_length=50, null=True, blank=True)
    os = models.CharField(max_length=50, null=True, blank=True)
    country = models.CharField(max_length=100, null=True, blank=True)
    region = models.CharField(max_length=100, null=True, blank=True)
    referrer = models.URLField(max_length=1024, null=True, blank=True)
    
    success = models.BooleanField(default=True)
    metadata = models.JSONField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['share_link']),
            models.Index(fields=['file']),
            models.Index(fields=['event_type']),
            models.Index(fields=['created_at']),
            models.Index(fields=['share_link', 'created_at']),
            models.Index(fields=['file', 'created_at']),
        ]

    def __str__(self):
        return f"{self.event_type} on {self.share_link.id} at {self.created_at}"
