import uuid
from django.db import models
from django.conf import settings

class FileStatus(models.TextChoices):
    PENDING = 'PENDING', 'Pending'
    UPLOADING = 'UPLOADING', 'Uploading'
    ACTIVE = 'ACTIVE', 'Active'
    FAILED = 'FAILED', 'Failed'
    DELETED = 'DELETED', 'Deleted'

class File(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='files')
    original_filename = models.CharField(max_length=255)
    storage_key = models.CharField(max_length=512, unique=True)
    file_size = models.BigIntegerField()
    content_type = models.CharField(max_length=128)
    checksum_sha256 = models.CharField(max_length=64, null=True, blank=True)
    status = models.CharField(max_length=20, choices=FileStatus.choices, default=FileStatus.PENDING)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    uploaded_at = models.DateTimeField(null=True, blank=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['owner', 'status']),
            models.Index(fields=['storage_key']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.original_filename} ({self.status})"
