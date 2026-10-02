from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings
from datetime import timedelta
from analytics.models import ShareEvent

class Command(BaseCommand):
    help = 'Cleans up old analytics ShareEvent records'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Print how many records would be deleted without actually deleting them',
        )

    def handle(self, *args, **options):
        retention_days = getattr(settings, 'ANALYTICS_RETENTION_DAYS', 90)
        cutoff_date = timezone.now() - timedelta(days=retention_days)

        events_to_delete = ShareEvent.objects.filter(created_at__lt=cutoff_date)
        count = events_to_delete.count()

        if options['dry_run']:
            self.stdout.write(self.style.SUCCESS(f'[DRY RUN] Would delete {count} ShareEvent records older than {retention_days} days.'))
        else:
            deleted_count, _ = events_to_delete.delete()
            self.stdout.write(self.style.SUCCESS(f'Successfully deleted {deleted_count} ShareEvent records older than {retention_days} days.'))
