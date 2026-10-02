import uuid
from django.db import models
from sharing.models import ShareLink

class QRCode(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    share_link = models.OneToOneField(ShareLink, on_delete=models.CASCADE, related_name='qr_code')
    storage_key = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"QRCode for ShareLink {self.share_link.id}"
