from __future__ import annotations

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from ...models import Message
from ...documents import MessageDocument


class Command(BaseCommand):
    help = "Sync messages from the last 1 day into Elasticsearch"

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=1,
            help="How many days back to sync",
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=500,
            help="Bulk indexing batch size",
        )

    def handle(self, *args, **options):
        days = options["days"]
        batch_size = options["batch_size"]
        since = timezone.now() - timedelta(days=days)

        queryset = (
            Message.objects.filter(created_at__gte=since)
            .select_related("session", "session__scenario", "session__user")
            .order_by("id")
        )
        total = queryset.count()
        self.stdout.write(self.style.NOTICE(f"Indexing {total} messages since {since.isoformat()}"))

        doc = MessageDocument()
        processed = 0
        buffer = []
        for message in queryset.iterator(chunk_size=batch_size):
            buffer.append(message)
            if len(buffer) >= batch_size:
                doc.update(buffer)
                processed += len(buffer)
                self.stdout.write(f"Indexed {processed}/{total}")
                buffer.clear()
        if buffer:
            doc.update(buffer)
            processed += len(buffer)
            self.stdout.write(f"Indexed {processed}/{total}")
        self.stdout.write(self.style.SUCCESS("Sync completed"))


