import os
import secrets
from django.conf import settings
from rest_framework.exceptions import ValidationError

ALLOWED_MIME_TYPES = {
    # Images
    'image/jpeg': ['.jpg', '.jpeg'],
    'image/png': ['.png'],
    'image/webp': ['.webp'],
    'image/gif': ['.gif'],
    # Documents
    'application/pdf': ['.pdf'],
    'application/msword': ['.doc'],
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
    'application/vnd.ms-excel': ['.xls'],
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
    'application/vnd.ms-powerpoint': ['.ppt'],
    'application/vnd.openxmlformats-officedocument.presentationml.presentation': ['.pptx'],
    # Other
    'text/plain': ['.txt'],
    'text/csv': ['.csv'],
    'application/zip': ['.zip'],
    'video/mp4': ['.mp4'],
    'video/quicktime': ['.mov'],
    'video/webm': ['.webm'],
    'audio/mpeg': ['.mp3'],
    'audio/wav': ['.wav'],
    'audio/x-m4a': ['.m4a']
}

def validate_file_type(content_type: str, filename: str):
    """Validates if the content type and extension are allowed."""
    if content_type not in ALLOWED_MIME_TYPES:
        raise ValidationError(f"Content type '{content_type}' is not allowed.")
    
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_MIME_TYPES[content_type]:
        raise ValidationError(f"Extension '{ext}' does not match content type '{content_type}'.")

def validate_file_size(file_size: int):
    """Validates if the file size is within limits."""
    if file_size <= 0:
        raise ValidationError("File size must be greater than 0.")
    if file_size > settings.MAX_FILE_SIZE:
        raise ValidationError(f"File size exceeds maximum allowed limit of {settings.MAX_FILE_SIZE} bytes.")

def generate_storage_key(user_id: int, filename: str) -> str:
    """Generates a secure, random storage key to prevent enumeration and path traversal."""
    ext = os.path.splitext(filename)[1].lower()
    random_id = secrets.token_urlsafe(32)
    # Ensure no path traversal tricks in extension
    safe_ext = ext.replace('/', '').replace('\\', '')
    return f"users/{user_id}/{random_id}{safe_ext}"
