from rest_framework import serializers
from .models import File

class FileSerializer(serializers.ModelSerializer):
    class Meta:
        model = File
        fields = [
            'id', 'original_filename', 'file_size', 'content_type',
            'status', 'created_at', 'uploaded_at'
        ]
        read_only_fields = fields

class UploadURLRequestSerializer(serializers.Serializer):
    filename = serializers.CharField(max_length=255)
    content_type = serializers.CharField(max_length=128)
    file_size = serializers.IntegerField(min_value=1)
