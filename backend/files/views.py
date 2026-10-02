import logging
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.generics import ListAPIView, RetrieveDestroyAPIView
from django.shortcuts import get_object_or_404
from django.conf import settings
from .models import File, FileStatus
from .serializers import FileSerializer, UploadURLRequestSerializer
from .validators import validate_file_type, validate_file_size, generate_storage_key
from .storage import StorageService
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

class UploadURLView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = UploadURLRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        filename = serializer.validated_data['filename']
        content_type = serializer.validated_data['content_type']
        file_size = serializer.validated_data['file_size']

        # 1. Validate constraints
        try:
            validate_file_size(file_size)
            validate_file_type(content_type, filename)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # 2. Check basic quotas (Files per user count limit logic placeholder)
        if File.objects.filter(owner=request.user, status__in=[FileStatus.ACTIVE]).count() >= settings.MAX_FILES_PER_USER:
            return Response({"error": "Maximum files quota reached."}, status=status.HTTP_403_FORBIDDEN)

        # 3. Generate storage key
        storage_key = generate_storage_key(request.user.id, filename)

        # 4. Create PENDING file record
        file_record = File.objects.create(
            owner=request.user,
            original_filename=filename,
            storage_key=storage_key,
            file_size=file_size,
            content_type=content_type,
            status=FileStatus.PENDING
        )

        # 5. Generate Presigned URL
        storage = StorageService()
        try:
            upload_url = storage.generate_upload_url(storage_key, content_type)
        except Exception as e:
            file_record.status = FileStatus.FAILED
            file_record.save()
            return Response({"error": "Failed to generate upload URL."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        file_record.status = FileStatus.UPLOADING
        file_record.save()

        return Response({
            "upload_url": upload_url,
            "file_id": file_record.id
        }, status=status.HTTP_201_CREATED)


class ConfirmUploadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        file_record = get_object_or_404(File, id=pk, owner=request.user)
        
        if file_record.status == FileStatus.ACTIVE:
            return Response({"message": "File is already active."}, status=status.HTTP_200_OK)

        storage = StorageService()
        try:
            meta = storage.verify_object(file_record.storage_key)
            actual_size = meta['content_length']
            
            validate_file_size(actual_size)

            file_record.file_size = actual_size
            file_record.status = FileStatus.ACTIVE
            file_record.uploaded_at = timezone.now()
            file_record.save()
            
            return Response(FileSerializer(file_record).data, status=status.HTTP_200_OK)

        except ClientError:
            file_record.status = FileStatus.FAILED
            file_record.save()
            return Response({"error": "Object not found in storage."}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            file_record.status = FileStatus.FAILED
            file_record.save()
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class FileListView(ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = FileSerializer

    def get_queryset(self):
        return File.objects.filter(owner=self.request.user, status=FileStatus.ACTIVE)


class FileDetailView(RetrieveDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = FileSerializer

    def get_queryset(self):
        return File.objects.filter(owner=self.request.user, status=FileStatus.ACTIVE)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        
        storage = StorageService()
        try:
            download_url = storage.generate_download_url(instance.storage_key)
            data = serializer.data
            data['download_url'] = download_url
            return Response(data)
        except Exception:
            return Response({"error": "Could not generate download URL."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def perform_destroy(self, instance):
        # Soft delete
        instance.status = FileStatus.DELETED
        instance.deleted_at = timezone.now()
        instance.save()
