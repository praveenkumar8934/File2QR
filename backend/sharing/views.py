import hashlib
import secrets
from django.utils import timezone
from django.db import transaction
from django.core.signing import TimestampSigner, BadSignature, SignatureExpired
from django.conf import settings
from rest_framework import viewsets, views, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.throttling import ScopedRateThrottle
from django.shortcuts import get_object_or_404
from .models import ShareLink
from .serializers import ShareLinkSerializer, PublicShareSerializer
from files.models import File, FileStatus
from files.storage import StorageService

def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode('utf-8')).hexdigest()

def _get_share_link(token: str) -> ShareLink:
    if not token:
        return None
    hashed_token = hash_token(token)
    try:
        share_link = ShareLink.objects.get(token_hash=hashed_token)
        if share_link.file.status != FileStatus.ACTIVE:
            return None
        return share_link
    except ShareLink.DoesNotExist:
        return None

def _get_active_share_link(token: str) -> ShareLink:
    share_link = _get_share_link(token)
    if share_link and share_link.is_active:
        return share_link
    return None

class ShareLinkViewSet(viewsets.ModelViewSet):
    serializer_class = ShareLinkSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_throttles(self):
        if self.action == 'regenerate_token':
            self.throttle_scope = 'regenerate'
            return [ScopedRateThrottle()]
        return super().get_throttles()

    def get_queryset(self):
        return ShareLink.objects.filter(owner=self.request.user)

    def create(self, request, *args, **kwargs):
        file_id = request.data.get('file_id')
        if not file_id:
            return Response({'error': 'file_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        file = get_object_or_404(File, id=file_id, owner=request.user)
        
        if file.status != FileStatus.ACTIVE:
            return Response({'error': 'File must be ACTIVE to be shared'}, status=status.HTTP_400_BAD_REQUEST)

        raw_token = secrets.token_urlsafe(32)
        hashed_token = hash_token(raw_token)
        
        password = request.data.get('password')
        from django.contrib.auth.hashers import make_password
        password_hash = make_password(password) if password else None

        expires_at = request.data.get('expires_at')
        max_downloads = request.data.get('max_downloads')

        share_link = ShareLink.objects.create(
            file=file,
            owner=request.user,
            token_hash=hashed_token,
            password_hash=password_hash,
            expires_at=expires_at,
            max_downloads=max_downloads
        )

        serializer = self.get_serializer(share_link, context={'raw_token': raw_token})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def revoke(self, request, pk=None):
        share_link = self.get_object()
        if not share_link.is_active:
            return Response({'status': 'already revoked'}, status=status.HTTP_200_OK)
        
        share_link.is_active = False
        share_link.revoked_at = timezone.now()
        share_link.save()
        return Response({'status': 'revoked'})

    @action(detail=True, methods=['post'], url_path='regenerate-token')
    def regenerate_token(self, request, pk=None):
        share_link = self.get_object()
        if not share_link.is_active:
            return Response({'error': 'Share link is inactive'}, status=status.HTTP_400_BAD_REQUEST)
        
        raw_token = secrets.token_urlsafe(32)
        hashed_token = hash_token(raw_token)
        
        share_link.token_hash = hashed_token
        share_link.save()
        
        # Invalidate old QR and regenerate
        from qr_codes.models import QRCode
        from qr_codes.services import QRGeneratorService
        try:
            qr = QRCode.objects.get(share_link=share_link)
            from analytics.services import generate_qr_signature
            sig = generate_qr_signature(str(qr.id), raw_token)
            share_url = f"{settings.FRONTEND_PUBLIC_URL.rstrip('/')}/f/{raw_token}?qr={qr.id}&sig={sig}"
            
            qr_service = QRGeneratorService()
            storage_key = qr_service.generate_qr(share_url)
            qr.storage_key = storage_key
            qr.is_active = True
            qr.save()
        except QRCode.DoesNotExist:
            pass

        serializer = self.get_serializer(share_link, context={'raw_token': raw_token})
        return Response(serializer.data)

class PublicShareResolveView(views.APIView):
    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    def get(self, request, token):
        share_link = _get_share_link(token)
        if not share_link:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
            
        from analytics.models import ShareEvent
        from analytics.services import record_share_event
            
        if not share_link.is_active:
            record_share_event(share_link, ShareEvent.EventType.REVOKED, request, success=False)
        elif share_link.expires_at and share_link.expires_at <= timezone.now():
            record_share_event(share_link, ShareEvent.EventType.EXPIRED, request, success=False)
        else:
            qr_id = request.query_params.get('qr')
            sig = request.query_params.get('sig')
            
            qr_code_obj = None
            is_valid_qr = False

            if qr_id and sig:
                from analytics.services import verify_qr_signature
                if verify_qr_signature(qr_id, token, sig):
                    from qr_codes.models import QRCode
                    try:
                        qr_code_obj = QRCode.objects.get(id=qr_id, share_link=share_link, is_active=True)
                        is_valid_qr = True
                    except QRCode.DoesNotExist:
                        pass
            
            # A valid share resolution always records a VIEW
            record_share_event(share_link, ShareEvent.EventType.VIEW, request, qr_code=qr_code_obj, success=True)
            
            # If it was a valid QR request, also record a QR_SCAN
            if is_valid_qr:
                record_share_event(share_link, ShareEvent.EventType.QR_SCAN, request, qr_code=qr_code_obj, success=True)
            
        serializer = PublicShareSerializer(share_link)
        return Response(serializer.data)

    def post(self, request, token=None):
        # Backward compatibility for POST /api/v1/public/share/resolve/
        t = request.data.get('token') if not token else token
        return self.get(request, t)

class PublicShareVerifyPasswordView(views.APIView):
    authentication_classes = []
    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'password_verify'

    def post(self, request, token):
        from analytics.models import ShareEvent
        from analytics.services import record_share_event

        share_link = _get_active_share_link(token)
        if not share_link:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
            
        if share_link.expires_at and share_link.expires_at <= timezone.now():
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
            
        password = request.data.get('password')
        from django.contrib.auth.hashers import check_password
        if not share_link.password_hash or not check_password(password, share_link.password_hash):
            record_share_event(share_link, ShareEvent.EventType.PASSWORD_FAILED, request, success=False)
            return Response({'error': 'Incorrect password'}, status=status.HTTP_403_FORBIDDEN)
            
        record_share_event(share_link, ShareEvent.EventType.PASSWORD_SUCCESS, request, success=True)
            
        signer = TimestampSigner()
        auth_value = f"{share_link.id}:{share_link.password_hash[:10]}"
        signed_auth = signer.sign(auth_value)
        
        response = Response({'status': 'verified'})
        response.set_cookie(
            key=f'share_auth_{token}',
            value=signed_auth,
            max_age=15 * 60, # 15 minutes
            httponly=True,
            samesite='Lax',
            secure=getattr(settings, 'SESSION_COOKIE_SECURE', False)
        )
        return response

class PublicShareDownloadView(views.APIView):
    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    def post(self, request, token):
        share_link = _get_active_share_link(token)
        if not share_link:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
            
        if share_link.expires_at and share_link.expires_at <= timezone.now():
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
            
        if share_link.password_hash:
            signed_auth = request.COOKIES.get(f'share_auth_{token}')
            if not signed_auth:
                return Response({'error': 'Password required'}, status=status.HTTP_403_FORBIDDEN)
            try:
                signer = TimestampSigner()
                auth_value = signer.unsign(signed_auth, max_age=15 * 60)
                expected_auth = f"{share_link.id}:{share_link.password_hash[:10]}"
                if auth_value != expected_auth:
                    return Response({'error': 'Invalid authorization'}, status=status.HTTP_403_FORBIDDEN)
            except SignatureExpired:
                return Response({'error': 'Authorization expired'}, status=status.HTTP_403_FORBIDDEN)
            except BadSignature:
                return Response({'error': 'Invalid authorization'}, status=status.HTTP_403_FORBIDDEN)
                
        with transaction.atomic():
            locked_share = ShareLink.objects.select_for_update().get(id=share_link.id)
            if locked_share.max_downloads is not None and locked_share.download_count >= locked_share.max_downloads:
                return Response({'error': 'Download limit reached'}, status=status.HTTP_403_FORBIDDEN)
                
            storage = StorageService()
            download_url = storage.generate_download_url(locked_share.file.storage_key)
            
            locked_share.download_count += 1
            locked_share.save(update_fields=['download_count'])
            
        from analytics.models import ShareEvent
        from analytics.services import record_share_event
        record_share_event(share_link, ShareEvent.EventType.DOWNLOAD, request, success=True)
            
        return Response({'download_url': download_url, 'expires_in': 300})
