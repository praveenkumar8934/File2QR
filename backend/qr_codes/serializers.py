from rest_framework import serializers
from .models import QRCode

class QRCodeSerializer(serializers.ModelSerializer):
    share_link_id = serializers.UUIDField(source='share_link.id', read_only=True)
    file_id = serializers.UUIDField(source='share_link.file.id', read_only=True)
    filename = serializers.CharField(source='share_link.file.original_filename', read_only=True)

    class Meta:
        model = QRCode
        fields = ['id', 'share_link_id', 'file_id', 'filename', 'is_active', 'created_at']
        read_only_fields = ['id', 'is_active', 'created_at']
