"""
Custom User model for SmartCNG.
Extends Django's AbstractUser with phone number and vehicle info.
"""
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Custom user model with additional CNG-relevant fields."""
    phone = models.CharField(max_length=15, blank=True, null=True)
    vehicle_number = models.CharField(max_length=20, blank=False, null=True)
    vehicle_type = models.CharField(
        max_length=20,
        choices=[
            ('car', 'Car'),
            ('auto', 'Auto Rickshaw'),
            ('taxi', 'Taxi'),
            ('bus', 'Bus'),
            ('other', 'Other'),
        ],
        default='car'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return f"{self.username} ({self.get_vehicle_type_display()})"
