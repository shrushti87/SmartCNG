"""
Models for CNG stations and crowd/queue updates.
"""
from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta


class Station(models.Model):
    """CNG filling station with location and status information."""

    STATUS_CHOICES = [
        ('available', 'Available'),
        ('low', 'Low Gas'),
        ('no_gas', 'No Gas'),
        ('closed', 'Closed'),
    ]

    name = models.CharField(max_length=255)
    address = models.TextField()
    latitude = models.FloatField()
    longitude = models.FloatField()
    place_id = models.CharField(max_length=255, unique=True, db_index=True)
    price_per_kg = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')
    phone = models.CharField(max_length=20, blank=True, null=True)
    opening_hours = models.TextField(blank=True, null=True, help_text='JSON formatted opening hours')
    description = models.TextField(blank=True, null=True)
    queue_time = models.IntegerField(default=0, help_text="Queue time in minutes")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'stations'
        ordering = ['name']
        verbose_name = 'CNG Station'
        verbose_name_plural = 'CNG Stations'

    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"

    @property
    def latest_queue(self):
        """Get the latest non-expired queue update for this station."""
        expiry_time = timezone.now() - timedelta(
            minutes=getattr(settings, 'QUEUE_UPDATE_EXPIRY_MINUTES', 60)
        )
        return self.queue_updates.filter(
            timestamp__gte=expiry_time
        ).order_by('-timestamp').first()

    @property
    def average_queue_length(self):
        """Average queue length from recent valid updates."""
        expiry_time = timezone.now() - timedelta(
            minutes=getattr(settings, 'QUEUE_UPDATE_EXPIRY_MINUTES', 60)
        )
        updates = self.queue_updates.filter(timestamp__gte=expiry_time)
        if not updates.exists():
            return 0
        return round(
            updates.aggregate(avg=models.Avg('queue_length'))['avg'] or 0
        )


class QueueUpdate(models.Model):
    """User-submitted queue/crowd update for a station."""

    AVAILABILITY_CHOICES = [
        ('available', 'Gas Available'),
        ('low', 'Low Gas'),
        ('no_gas', 'No Gas'),
    ]

    station = models.ForeignKey(
        Station,
        on_delete=models.CASCADE,
        related_name='queue_updates'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='queue_updates'
    )
    queue_length = models.PositiveIntegerField(
        help_text='Estimated number of vehicles in queue'
    )
    availability = models.CharField(
        max_length=20,
        choices=AVAILABILITY_CHOICES,
        default='available'
    )
    comment = models.TextField(blank=True, null=True)
    upvotes = models.PositiveIntegerField(default=0)
    downvotes = models.PositiveIntegerField(default=0)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'queue_updates'
        ordering = ['-timestamp']
        verbose_name = 'Queue Update'
        verbose_name_plural = 'Queue Updates'

    def __str__(self):
        return f"{self.station.name} - {self.queue_length} vehicles ({self.get_availability_display()})"

    @property
    def is_expired(self):
        """Check if this update has expired."""
        expiry_time = timezone.now() - timedelta(
            minutes=getattr(settings, 'QUEUE_UPDATE_EXPIRY_MINUTES', 60)
        )
        return self.timestamp < expiry_time

    @property
    def reliability_score(self):
        """Calculate reliability score based on votes."""
        total = self.upvotes + self.downvotes
        if total == 0:
            return 50  # neutral
        return round((self.upvotes / total) * 100)


class QueueVote(models.Model):
    """Track user votes on queue updates to prevent duplicate voting."""
    VOTE_CHOICES = [
        ('up', 'Upvote'),
        ('down', 'Downvote'),
    ]

    update = models.ForeignKey(
        QueueUpdate,
        on_delete=models.CASCADE,
        related_name='votes'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='queue_votes'
    )
    vote_type = models.CharField(max_length=4, choices=VOTE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'queue_votes'
        unique_together = ('update', 'user')

    def __str__(self):
        return f"{self.user.username} - {self.vote_type} on update #{self.update.id}"


class Favorite(models.Model):
    """User's favorite/saved stations."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='favorites'
    )
    station = models.ForeignKey(
        Station,
        on_delete=models.CASCADE,
        related_name='favorited_by'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'favorites'
        unique_together = ('user', 'station')

    def __str__(self):
        return f"{self.user.username} → {self.station.name}"
