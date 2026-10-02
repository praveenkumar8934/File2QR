from rest_framework import serializers
from .models import ShareEvent
from sharing.serializers import ShareLinkSerializer
from files.serializers import FileSerializer

class ShareEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShareEvent
        fields = [
            'id',
            'share_link',
            'file',
            'qr_code',
            'event_type',
            'created_at',
            'device_type',
            'browser',
            'os',
            'country',
            'region',
            'referrer',
            'success'
        ]
