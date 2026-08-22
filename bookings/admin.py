"""
Admin configuration for bookings app.
"""
from django.contrib import admin
from .models import Slot, Booking


@admin.register(Slot)
class SlotAdmin(admin.ModelAdmin):
    """Admin for time slot management."""
    list_display = ('station', 'start_time', 'end_time', 'max_capacity', 'is_active')
    list_filter = ('station', 'is_active')
    search_fields = ('station__name',)
    list_editable = ('max_capacity', 'is_active')


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    """Admin for booking management."""
    list_display = (
        'booking_id', 'user', 'station', 'slot', 'date',
        'status', 'vehicle_number', 'created_at'
    )
    list_filter = ('status', 'date', 'station')
    search_fields = ('booking_id', 'user__username', 'station__name', 'vehicle_number')
    list_editable = ('status',)
    readonly_fields = ('booking_id', 'created_at', 'updated_at')
    date_hierarchy = 'date'
