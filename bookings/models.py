"""
Models for slot booking system.
"""
import uuid
from django.db import models
from django.conf import settings
from stations.models import Station


class Slot(models.Model):
    """A time slot at a station that users can book."""
    station = models.ForeignKey(
        Station,
        on_delete=models.CASCADE,
        related_name='slots'
    )
    start_time = models.TimeField()
    end_time = models.TimeField()
    max_capacity = models.PositiveIntegerField(default=10)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'slots'
        ordering = ['start_time']
        verbose_name = 'Time Slot'
        verbose_name_plural = 'Time Slots'
        unique_together = ('station', 'start_time', 'end_time')

    def __str__(self):
        return f"{self.station.name}: {self.start_time.strftime('%H:%M')} - {self.end_time.strftime('%H:%M')} (Cap: {self.max_capacity})"

    def bookings_for_date(self, date):
        """Get confirmed bookings count for a specific date."""
        return self.bookings.filter(
            date=date,
            status__in=['confirmed', 'pending']
        ).count()

    def available_capacity(self, date):
        """Get remaining capacity for a specific date."""
        return self.max_capacity - self.bookings_for_date(date)

    def is_available(self, date):
        """Check if this slot has available capacity for a date."""
        return self.available_capacity(date) > 0


class Booking(models.Model):
    """A user's booking for a specific slot at a station."""

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('no_show', 'No Show'),
    ]

    booking_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='bookings'
    )
    station = models.ForeignKey(
        Station,
        on_delete=models.CASCADE,
        related_name='bookings'
    )
    slot = models.ForeignKey(
        Slot,
        on_delete=models.CASCADE,
        related_name='bookings'
    )
    date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    vehicle_number = models.CharField(max_length=20, blank=False, null=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'bookings'
        ordering = ['-created_at']
        verbose_name = 'Booking'
        verbose_name_plural = 'Bookings'
        # Prevent duplicate bookings: same user, same slot, same date
        unique_together = ('user', 'slot', 'date')

    def __str__(self):
        return f"Booking {self.booking_id} - {self.user.username} at {self.station.name}"

    @property
    def token(self):
        """Short booking token for display."""
        return str(self.booking_id)[:8].upper()
