from django.urls import path
from .views import (
    AnalyticsOverviewView,
    AnalyticsTimeseriesView,
    FileAnalyticsView,
    ShareAnalyticsDetailView,
    QRAnalyticsDetailView
)

urlpatterns = [
    path('overview/', AnalyticsOverviewView.as_view(), name='analytics-overview'),
    path('timeseries/', AnalyticsTimeseriesView.as_view(), name='analytics-timeseries'),
    path('files/', FileAnalyticsView.as_view(), name='analytics-files'),
    path('shares/<uuid:pk>/', ShareAnalyticsDetailView.as_view(), name='analytics-share-detail'),
    path('qr/<uuid:pk>/', QRAnalyticsDetailView.as_view(), name='analytics-qr-detail'),
]
