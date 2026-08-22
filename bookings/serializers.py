"""
Serializers for slot booking system.
"""
from rest_framework import serializers
from .models import Slot, Booking


class SlotSerializer(serializers.ModelSerializer):
    """Serializer for time slots with availability info."""
    available_capacity = serializers.SerializerMethodField()
    station_name = serializers.CharField(source='station.name', read_only=True)

    class Meta:
        model = Slot
        fields = (
            'id', 'station', 'station_name', 'start_time', 'end_time',
            'max_capacity', 'available_capacity', 'is_active'
        )

    def get_available_capacity(self, obj):
        """Get available capacity for requested date."""
        request = self.context.get('request')
        if request:
            date = request.query_params.get('date')
            if date:
                from datetime import datetime
                try:
                    date_obj = datetime.strptime(date, '%Y-%m-%d').date()
                    return obj.available_capacity(date_obj)
                except ValueError:
                    pass
        return obj.max_capacity


class BookingSerializer(serializers.ModelSerializer):
    """Serializer for booking display."""
    station_name = serializers.CharField(source='station.name', read_only=True)
    station_address = serializers.CharField(source='station.address', read_only=True)
    slot_time = serializers.SerializerMethodField()
    token = serializers.CharField(read_only=True)

    class Meta:
        model = Booking
        fields = (
            'id', 'booking_id', 'token', 'station', 'station_name',
            'station_address', 'slot', 'slot_time', 'date', 'status',
            'vehicle_number', 'notes', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'booking_id', 'token', 'status', 'created_at', 'updated_at')

    def get_slot_time(self, obj):
        return f"{obj.slot.start_time.strftime('%H:%M')} - {obj.slot.end_time.strftime('%H:%M')}"


class BookingCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating bookings with validation."""

    class Meta:
        model = Booking
        fields = ('station', 'slot', 'date', 'vehicle_number', 'notes')

    def validate_vehicle_number(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Vehicle number is required.")
        return value

    def validate(self, attrs):
        slot = attrs['slot']
        date = attrs['date']
        user = self.context['request'].user

        # Prevent admins from booking
        if user.is_staff or user.is_superuser:
            raise serializers.ValidationError(
                "Administrators are not allowed to create bookings."
            )

        # Validate slot belongs to station
        if slot.station_id != attrs['station'].id:
            raise serializers.ValidationError(
                "Selected slot does not belong to the selected station."
            )

        # Validate slot is active
        if not slot.is_active:
            raise serializers.ValidationError("This slot is not available.")

        # Check capacity
        if not slot.is_available(date):
            raise serializers.ValidationError(
                "This slot is fully booked for the selected date."
            )

        # Check for duplicate booking
        if Booking.objects.filter(
            user=user, slot=slot, date=date,
            status__in=['pending', 'confirmed']
        ).exists():
            raise serializers.ValidationError(
                "You already have a booking for this slot on this date."
            )

        # Check date is not in the past
        from django.utils import timezone
        if date < timezone.now().date():
            raise serializers.ValidationError("Cannot book for a past date.")

        return attrs

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        validated_data['status'] = 'confirmed'
        return super().create(validated_data)
