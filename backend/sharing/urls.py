from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ShareLinkViewSet, 
    PublicShareResolveView,
    PublicShareVerifyPasswordView,
    PublicShareDownloadView
)

router = DefaultRouter()
router.register(r'shares', ShareLinkViewSet, basename='sharelink')

urlpatterns = [
    path('', include(router.urls)),
    path('public/share/resolve/', PublicShareResolveView.as_view(), name='public-share-resolve'),
    path('public/share/<str:token>/', PublicShareResolveView.as_view(), name='public-share-resolve-get'),
    path('public/share/<str:token>/verify-password/', PublicShareVerifyPasswordView.as_view(), name='public-share-verify'),
    path('public/share/<str:token>/download/', PublicShareDownloadView.as_view(), name='public-share-download'),
]
