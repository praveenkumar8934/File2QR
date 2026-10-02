from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from django.conf import settings
from .models import QRCode
from .serializers import QRCodeSerializer
from .services import QRGeneratorService
from sharing.models import ShareLink
from files.storage import StorageService

class QRCodeViewSet(viewsets.ModelViewSet):
    serializer_class = QRCodeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Only return QRs for ShareLinks owned by the authenticated user
        return QRCode.objects.filter(share_link__owner=self.request.user)

    def create(self, request, *args, **kwargs):
        share_link_id = request.data.get('share_link_id')
        if not share_link_id:
            return Response({'error': 'share_link_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        share_link = get_object_or_404(ShareLink, id=share_link_id, owner=request.user)
        
        if not share_link.is_active:
            return Response({'error': 'Share link must be active to generate a QR code'}, status=status.HTTP_400_BAD_REQUEST)

        # Check for existing active QR
        try:
            qr = QRCode.objects.get(share_link=share_link)
            if not qr.is_active:
                # If it exists but is inactive, we could reactivate it or regenerate. Let's reactivate.
                qr.is_active = True
                qr.save()
            serializer = self.get_serializer(qr)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except QRCode.DoesNotExist:
            pass

        # Generate a new QR
        # To generate the QR, we need the share_url. Since we only store token_hash, we can't reliably reconstruct the full share_url 
        # unless the frontend passes the raw_token, OR we rethink.
        # Wait, the instruction said: "If the raw token is no longer available later, do NOT attempt to recover it from the database."
        # If the frontend asks us to generate a QR, it must provide the raw token it saved, OR we can't do it.
        # Let's require the `raw_token` to be passed in the request.
        
        raw_token = request.data.get('raw_token')
        if not raw_token:
            return Response({'error': 'raw_token is required to generate a QR code'}, status=status.HTTP_400_BAD_REQUEST)

        # Validate the raw_token actually matches this share link
        import hashlib
        hashed = hashlib.sha256(raw_token.encode('utf-8')).hexdigest()
        if hashed != share_link.token_hash:
            return Response({'error': 'Invalid raw_token for this share link'}, status=status.HTTP_400_BAD_REQUEST)

        # Create QR object first to get the ID for the signature
        qr_code = QRCode.objects.create(
            share_link=share_link,
            storage_key='' # temporary
        )

        from analytics.services import generate_qr_signature
        sig = generate_qr_signature(str(qr_code.id), raw_token)
        share_url = f"{settings.FRONTEND_PUBLIC_URL.rstrip('/')}/f/{raw_token}?qr={qr_code.id}&sig={sig}"
        
        qr_service = QRGeneratorService()
        storage_key = qr_service.generate_qr(share_url)

        qr_code.storage_key = storage_key
        qr_code.save(update_fields=['storage_key'])

        serializer = self.get_serializer(qr_code)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        qr_code = self.get_object()
        
        if not qr_code.is_active:
            return Response({'error': 'QR Code is deactivated'}, status=status.HTTP_400_BAD_REQUEST)

        storage = StorageService()
        download_url = storage.generate_download_url(qr_code.storage_key)
        
        return Response({'download_url': download_url})

    def destroy(self, request, *args, **kwargs):
        # Soft deactivate instead of hard delete
        qr_code = self.get_object()
        qr_code.is_active = False
        qr_code.save()
        return Response({'status': 'deactivated'}, status=status.HTTP_200_OK)
