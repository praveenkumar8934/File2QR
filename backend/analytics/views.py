from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Count, Q, F
from django.db.models.functions import TruncDate
from rest_framework import views, status, permissions
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from .models import ShareEvent
from sharing.models import ShareLink
from files.models import File
from qr_codes.models import QRCode

def get_date_range(request):
    """
    Returns (start_date, end_date) ensuring max 90 days.
    Defaults to last 30 days.
    """
    to_date_str = request.query_params.get('to')
    from_date_str = request.query_params.get('from')
    
    now = timezone.now()
    end_date = now
    
    if to_date_str:
        try:
            parsed = datetime.strptime(to_date_str, '%Y-%m-%d').date()
            end_date = timezone.make_aware(datetime.combine(parsed, datetime.max.time()))
        except ValueError:
            pass
            
    if from_date_str:
        try:
            parsed = datetime.strptime(from_date_str, '%Y-%m-%d').date()
            start_date = timezone.make_aware(datetime.combine(parsed, datetime.min.time()))
        except ValueError:
            start_date = end_date - timedelta(days=30)
    else:
        start_date = end_date - timedelta(days=30)
        
    if start_date > end_date:
        start_date = end_date - timedelta(days=30)
        
    if (end_date - start_date).days > 90:
        start_date = end_date - timedelta(days=90)
        
    return start_date, end_date

class AnalyticsBaseView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'analytics'

class AnalyticsOverviewView(AnalyticsBaseView):
    def get(self, request):
        start_date, end_date = get_date_range(request)
        
        # Only events for user's shares
        base_qs = ShareEvent.objects.filter(
            share_link__owner=request.user,
            created_at__gte=start_date,
            created_at__lte=end_date
        )
        
        # Aggregations
        aggregates = base_qs.aggregate(
            total_views=Count('id', filter=Q(event_type=ShareEvent.EventType.VIEW, success=True)),
            total_downloads=Count('id', filter=Q(event_type=ShareEvent.EventType.DOWNLOAD, success=True)),
            total_qr_scans=Count('id', filter=Q(event_type=ShareEvent.EventType.QR_SCAN, success=True)),
            unique_visitors=Count('ip_hash', distinct=True)
        )
        
        # Counts of shares
        shares = ShareLink.objects.filter(owner=request.user)
        active_shares = shares.filter(is_active=True).count()
        revoked_shares = shares.filter(is_active=False).count()
        
        now = timezone.now()
        expired_shares = shares.filter(expires_at__lte=now).count()

        return Response({
            'total_views': aggregates['total_views'],
            'total_downloads': aggregates['total_downloads'],
            'total_qr_scans': aggregates['total_qr_scans'],
            'unique_visitors': aggregates['unique_visitors'],
            'active_shares': active_shares,
            'expired_shares': expired_shares,
            'revoked_shares': revoked_shares,
            'date_range': {
                'from': start_date.strftime('%Y-%m-%d'),
                'to': end_date.strftime('%Y-%m-%d')
            }
        })

class AnalyticsTimeseriesView(AnalyticsBaseView):
    def get(self, request):
        start_date, end_date = get_date_range(request)
        
        base_qs = ShareEvent.objects.filter(
            share_link__owner=request.user,
            created_at__gte=start_date,
            created_at__lte=end_date
        )
        
        timeseries = base_qs.annotate(
            date=TruncDate('created_at')
        ).values('date').annotate(
            views=Count('id', filter=Q(event_type=ShareEvent.EventType.VIEW, success=True)),
            downloads=Count('id', filter=Q(event_type=ShareEvent.EventType.DOWNLOAD, success=True)),
            qr_scans=Count('id', filter=Q(event_type=ShareEvent.EventType.QR_SCAN, success=True)),
        ).order_by('date')
        
        # Format as list of dicts
        result = []
        for entry in timeseries:
            result.append({
                'date': entry['date'].strftime('%Y-%m-%d'),
                'views': entry['views'],
                'downloads': entry['downloads'],
                'qr_scans': entry['qr_scans']
            })
            
        return Response(result)

class FileAnalyticsView(AnalyticsBaseView):
    def get(self, request):
        start_date, end_date = get_date_range(request)
        
        # Return per-file stats for the user
        files = File.objects.filter(owner=request.user)
        
        # We can annotate directly, but doing it via events is safer for distinct
        events = ShareEvent.objects.filter(
            file__owner=request.user,
            created_at__gte=start_date,
            created_at__lte=end_date
        )
        
        file_stats = events.values('file_id', 'file__name').annotate(
            views=Count('id', filter=Q(event_type=ShareEvent.EventType.VIEW, success=True)),
            downloads=Count('id', filter=Q(event_type=ShareEvent.EventType.DOWNLOAD, success=True)),
            qr_scans=Count('id', filter=Q(event_type=ShareEvent.EventType.QR_SCAN, success=True)),
            unique_visitors=Count('ip_hash', distinct=True)
        ).order_by('-views')
        
        result = []
        for stat in file_stats:
            result.append({
                'file_id': stat['file_id'],
                'filename': stat['file__name'],
                'views': stat['views'],
                'downloads': stat['downloads'],
                'qr_scans': stat['qr_scans'],
                'unique_visitors': stat['unique_visitors']
            })
            
        return Response(result)

class ShareAnalyticsDetailView(AnalyticsBaseView):
    def get(self, request, pk):
        start_date, end_date = get_date_range(request)
        
        try:
            share = ShareLink.objects.get(id=pk, owner=request.user)
        except ShareLink.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
            
        events = ShareEvent.objects.filter(
            share_link=share,
            created_at__gte=start_date,
            created_at__lte=end_date
        )
        
        aggs = events.aggregate(
            views=Count('id', filter=Q(event_type=ShareEvent.EventType.VIEW, success=True)),
            downloads=Count('id', filter=Q(event_type=ShareEvent.EventType.DOWNLOAD, success=True)),
            qr_scans=Count('id', filter=Q(event_type=ShareEvent.EventType.QR_SCAN, success=True)),
            unique_visitors=Count('ip_hash', distinct=True),
            password_success=Count('id', filter=Q(event_type=ShareEvent.EventType.PASSWORD_SUCCESS)),
            password_failed=Count('id', filter=Q(event_type=ShareEvent.EventType.PASSWORD_FAILED)),
        )
        
        last_accessed = events.order_by('-created_at').first()
        last_accessed_date = last_accessed.created_at if last_accessed else None
        
        # Recent activity (timeline)
        recent_events = events.order_by('-created_at')[:10]
        timeline = []
        for e in recent_events:
            timeline.append({
                'event_type': e.event_type,
                'date': e.created_at.isoformat(),
                'device': e.device_type,
                'browser': e.browser,
                'country': e.country,
                'success': e.success
            })
            
        return Response({
            'share_id': str(share.id),
            'views': aggs['views'],
            'downloads': aggs['downloads'],
            'qr_scans': aggs['qr_scans'],
            'unique_visitors': aggs['unique_visitors'],
            'password_success': aggs['password_success'],
            'password_failed': aggs['password_failed'],
            'last_accessed': last_accessed_date.isoformat() if last_accessed_date else None,
            'timeline': timeline
        })

class QRAnalyticsDetailView(AnalyticsBaseView):
    def get(self, request, pk):
        start_date, end_date = get_date_range(request)
        
        try:
            qr = QRCode.objects.get(id=pk, share_link__owner=request.user)
        except QRCode.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
            
        events = ShareEvent.objects.filter(
            qr_code=qr,
            event_type=ShareEvent.EventType.QR_SCAN,
            created_at__gte=start_date,
            created_at__lte=end_date
        )
        
        aggs = events.aggregate(
            total_scans=Count('id'),
            unique_visitors=Count('ip_hash', distinct=True)
        )
        
        # Breakdown by device
        device_breakdown = events.values('device_type').annotate(count=Count('id'))
        
        # Breakdown by browser
        browser_breakdown = events.values('browser').annotate(count=Count('id'))
        
        # Breakdown by os
        os_breakdown = events.values('os').annotate(count=Count('id'))
        
        last_scan = events.order_by('-created_at').first()
        last_scan_date = last_scan.created_at if last_scan else None
        
        return Response({
            'qr_id': str(qr.id),
            'total_scans': aggs['total_scans'],
            'unique_visitors': aggs['unique_visitors'],
            'device_breakdown': list(device_breakdown),
            'browser_breakdown': list(browser_breakdown),
            'os_breakdown': list(os_breakdown),
            'last_scan': last_scan_date.isoformat() if last_scan_date else None
        })
