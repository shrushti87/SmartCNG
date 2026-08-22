"""
Management command to seed time slots for all stations.
Usage: python manage.py seed_slots
"""
from datetime import time
from django.core.management.base import BaseCommand
from stations.models import Station
from bookings.models import Slot


class Command(BaseCommand):
    help = 'Create default time slots for all stations'

    def handle(self, *args, **options):
        # Default time slots (30-minute intervals from 6 AM to 10 PM)
        time_slots = []
        for hour in range(6, 22):
            time_slots.append((time(hour, 0), time(hour, 30)))
            time_slots.append((time(hour, 30), time(hour + 1 if hour < 23 else 0, 0)))

        stations = Station.objects.filter(is_active=True)
        created_count = 0

        for station in stations:
            for start, end in time_slots:
                _, created = Slot.objects.get_or_create(
                    station=station,
                    start_time=start,
                    end_time=end,
                    defaults={'max_capacity': 10}
                )
                if created:
                    created_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'Created {created_count} slots across {stations.count()} stations'
        ))
