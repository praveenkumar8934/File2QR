from rest_framework import serializers
from .models import ShareLink
from django.conf import settings

from django.contrib.auth.hashers import make_password

class ShareLinkSerializer(serializers.ModelSerializer):
    file_id = serializers.UUIDField(source='file.id', read_only=True)
    share_url = serializers.SerializerMethodField()
    password = serializers.CharField(write_only=True, required=False, allow_null=True, allow_blank=True)

    class Meta:
        model = ShareLink
        fields = ['id', 'file_id', 'share_url', 'is_active', 'created_at', 'revoked_at', 
                  'expires_at', 'max_downloads', 'download_count', 'password']
        read_only_fields = ['id', 'share_url', 'is_active', 'created_at', 'revoked_at', 'download_count', 'file_id']

    def update(self, instance, validated_data):
        if 'password' in validated_data:
            password = validated_data.pop('password')
            if password:
                instance.password_hash = make_password(password)
            else:
                instance.password_hash = None
        return super().update(instance, validated_data)

    def get_share_url(self, obj):
        # We can't generate the public URL directly from the DB because we don't store the raw token.
        # So we only return a share_url if a raw_token was passed in the context (during creation).
        raw_token = self.context.get('raw_token')
        if raw_token:
            return f"{settings.FRONTEND_PUBLIC_URL.rstrip('/')}/f/{raw_token}"
        return None

class PublicShareSerializer(serializers.Serializer):
    filename = serializers.CharField(source='file.original_filename')
    content_type = serializers.CharField(source='file.content_type')
    file_size = serializers.IntegerField(source='file.file_size')
    created_at = serializers.DateTimeField()
    expires_at = serializers.DateTimeField()
    password_required = serializers.SerializerMethodField()

    def get_password_required(self, obj):
        return bool(obj.password_hash)
