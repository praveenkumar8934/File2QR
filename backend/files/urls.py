from django.urls import path
from .views import UploadURLView, ConfirmUploadView, FileListView, FileDetailView

urlpatterns = [
    path('upload-url/', UploadURLView.as_view(), name='upload_url'),
    path('<uuid:pk>/confirm-upload/', ConfirmUploadView.as_view(), name='confirm_upload'),
    path('', FileListView.as_view(), name='file_list'),
    path('<uuid:pk>/', FileDetailView.as_view(), name='file_detail'),
]
