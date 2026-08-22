"""
Views for slot booking system.
"""
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Slot, Booking
from .serializers import SlotSerializer, BookingSerializer, BookingCreateSerializer


class SlotListView(generics.ListAPIView):
    """
    GET /api/slots/<station_id>/?date=YYYY-MM-DD
    List available slots for a station on a specific date.
    """
    serializer_class = SlotSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        station_id = self.kwargs['station_id']
        return Slot.objects.filter(
            station_id=station_id,
            is_active=True
        )


class BookingCreateView(generics.CreateAPIView):
    """
    POST /api/booking/create/
    Create a new booking.
    """
    serializer_class = BookingCreateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        booking = serializer.save()

        return Response({
            'message': 'Booking confirmed!',
            'booking': BookingSerializer(booking).data
        }, status=status.HTTP_201_CREATED)


class UserBookingsView(generics.ListAPIView):
    """
    GET /api/booking/user/
    List all bookings for the authenticated user.
    """
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Booking.objects.filter(user=self.request.user)


class BookingCancelView(APIView):
    """
    POST /api/booking/cancel/<booking_id>/
    Cancel a booking.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, booking_id):
        try:
            booking = Booking.objects.get(
                booking_id=booking_id,
                user=request.user
            )
        except Booking.DoesNotExist:
            return Response(
                {'error': 'Booking not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        if booking.status in ['cancelled', 'completed']:
            return Response(
                {'error': f'Booking is already {booking.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        booking.status = 'cancelled'
        booking.save()
        return Response({
            'message': 'Booking cancelled successfully',
            'booking': BookingSerializer(booking).data
        })


class BookingDetailView(generics.RetrieveAPIView):
    """
    GET /api/booking/<booking_id>/
    Get booking details.
    """
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'booking_id'

    def get_queryset(self):
        return Booking.objects.filter(user=self.request.user)
