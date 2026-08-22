"""
Views for CNG stations: list, nearby, detail, queue updates, favorites, and directions proxy.
"""
import math
import requests as http_requests
from django.conf import settings
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta
from rest_framework import generics, permissions, status, views
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from .models import Station, QueueUpdate, QueueVote, Favorite
from .serializers import (
    StationSerializer, StationListSerializer,
    QueueUpdateSerializer, QueueUpdateCreateSerializer,
    QueueVoteSerializer, FavoriteSerializer,
)


def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the great-circle distance between two points
    on Earth using the Haversine formula.
    Returns distance in kilometers.
    """
    R = 6371  # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) *
         math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c, 2)


# ─── Station Views ───────────────────────────────────────────────────

class StationListView(generics.ListAPIView):
    """
    GET /api/stations/
    List all active CNG stations. Supports search by name and area.
    """
    serializer_class = StationListSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        queryset = Station.objects.filter(is_active=True)
        # Search by name or address
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(address__icontains=search)
            )
        return queryset


class StationDetailView(generics.RetrieveAPIView):
    """
    GET /api/stations/<id>/
    Get detailed station info.
    """
    queryset = Station.objects.filter(is_active=True)
    serializer_class = StationSerializer
    permission_classes = [permissions.AllowAny]


class NearbyStationsView(views.APIView):
    """
    GET /api/stations/nearby/?lat=<lat>&lng=<lng>&radius=<km>
    Find nearby stations sorted by distance, queue, and availability.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        lat = request.query_params.get('lat')
        lng = request.query_params.get('lng')
        radius = float(request.query_params.get('radius', 25))  # default 25km
        sort_by = request.query_params.get('sort', 'distance')  # distance, queue, smart

        if not lat or not lng:
            return Response(
                {'error': 'lat and lng parameters are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user_lat = float(lat)
            user_lng = float(lng)
        except ValueError:
            return Response(
                {'error': 'Invalid lat/lng values'},
                status=status.HTTP_400_BAD_REQUEST
            )

        stations = Station.objects.filter(is_active=True)
        results = []

        for station in stations:
            dist = haversine_distance(user_lat, user_lng, station.latitude, station.longitude)
            if dist <= radius:
                station.distance = dist
                results.append(station)

        # Smart sorting
        if sort_by == 'queue':
            results.sort(key=lambda s: (s.average_queue_length, s.distance))
        elif sort_by == 'smart':
            # Best Station Now: weighted by distance + queue + availability
            def smart_score(s):
                queue = s.average_queue_length
                avail = s.latest_queue
                avail_penalty = 0
                if avail:
                    if avail.availability == 'low':
                        avail_penalty = 5
                    elif avail.availability == 'no_gas':
                        avail_penalty = 100
                return s.distance + (queue * 0.5) + avail_penalty
            results.sort(key=smart_score)
        else:
            results.sort(key=lambda s: s.distance)

        serializer = StationListSerializer(
            results, many=True, context={'request': request}
        )
        data = serializer.data
        # Inject computed distance
        for i, station in enumerate(results):
            data[i]['distance'] = station.distance

        return Response({
            'count': len(data),
            'stations': data
        })


class BestStationView(views.APIView):
    """
    GET /api/stations/best/?lat=<lat>&lng=<lng>
    Recommend the single best station based on distance + queue + availability.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        lat = request.query_params.get('lat')
        lng = request.query_params.get('lng')

        if not lat or not lng:
            return Response(
                {'error': 'lat and lng parameters are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user_lat = float(lat)
            user_lng = float(lng)
        except ValueError:
            return Response({'error': 'Invalid lat/lng'}, status=status.HTTP_400_BAD_REQUEST)

        stations = Station.objects.filter(is_active=True)
        best = None
        best_score = float('inf')

        for station in stations:
            dist = haversine_distance(user_lat, user_lng, station.latitude, station.longitude)
            if dist > 50:  # Skip stations beyond 50km
                continue
            queue = station.average_queue_length
            latest = station.latest_queue
            avail_penalty = 0
            if latest:
                if latest.availability == 'low':
                    avail_penalty = 5
                elif latest.availability == 'no_gas':
                    avail_penalty = 100

            score = dist + (queue * 0.5) + avail_penalty
            if score < best_score:
                best_score = score
                best = station
                best.distance = dist

        if not best:
            return Response({'message': 'No stations found nearby'}, status=status.HTTP_404_NOT_FOUND)

        serializer = StationSerializer(best, context={'request': request})
        data = serializer.data
        data['distance'] = best.distance
        data['smart_score'] = round(best_score, 2)
        return Response(data)


# ─── Queue Update Views ─────────────────────────────────────────────

class QueueUpdateCreateView(generics.CreateAPIView):
    """
    POST /api/queue/update/
    Submit a queue/crowd update for a station.
    """
    serializer_class = QueueUpdateCreateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        update = serializer.save()
        # Update station status based on this report
        station = update.station
        station.status = update.availability
        station.save(update_fields=['status'])


class QueueUpdateLatestView(views.APIView):
    """
    GET /api/queue/latest/<station_id>/
    Get latest non-expired queue updates for a station.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, station_id):
        expiry_time = timezone.now() - timedelta(
            minutes=getattr(settings, 'QUEUE_UPDATE_EXPIRY_MINUTES', 60)
        )
        updates = QueueUpdate.objects.filter(
            station_id=station_id,
            timestamp__gte=expiry_time
        ).order_by('-timestamp')[:20]

        serializer = QueueUpdateSerializer(
            updates, many=True, context={'request': request}
        )
        return Response({
            'count': len(serializer.data),
            'updates': serializer.data
        })


class QueueVoteView(views.APIView):
    """
    POST /api/queue/vote/<update_id>/
    Upvote or downvote a queue update.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, update_id):
        serializer = QueueVoteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        vote_type = serializer.validated_data['vote_type']

        try:
            update = QueueUpdate.objects.get(id=update_id)
        except QueueUpdate.DoesNotExist:
            return Response(
                {'error': 'Update not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Check for existing vote
        existing_vote = QueueVote.objects.filter(
            update=update, user=request.user
        ).first()

        if existing_vote:
            if existing_vote.vote_type == vote_type:
                # Remove vote (toggle off)
                if vote_type == 'up':
                    update.upvotes = max(0, update.upvotes - 1)
                else:
                    update.downvotes = max(0, update.downvotes - 1)
                update.save()
                existing_vote.delete()
                return Response({'message': 'Vote removed'})
            else:
                # Change vote
                if vote_type == 'up':
                    update.upvotes += 1
                    update.downvotes = max(0, update.downvotes - 1)
                else:
                    update.downvotes += 1
                    update.upvotes = max(0, update.upvotes - 1)
                existing_vote.vote_type = vote_type
                existing_vote.save()
                update.save()
                return Response({'message': 'Vote changed'})
        else:
            # New vote
            QueueVote.objects.create(
                update=update, user=request.user, vote_type=vote_type
            )
            if vote_type == 'up':
                update.upvotes += 1
            else:
                update.downvotes += 1
            update.save()
            return Response({'message': 'Vote recorded'})


# ─── Favorite Views ─────────────────────────────────────────────────

class FavoriteListCreateView(generics.ListCreateAPIView):
    """
    GET /api/favorites/ - List user's favorites
    POST /api/favorites/ - Add a station to favorites
    """
    serializer_class = FavoriteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Favorite.objects.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        station_id = request.data.get('station')
        # Check if already favorited
        if Favorite.objects.filter(user=request.user, station_id=station_id).exists():
            return Response(
                {'error': 'Station already in favorites'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().create(request, *args, **kwargs)


class FavoriteDeleteView(generics.DestroyAPIView):
    """
    DELETE /api/favorites/<station_id>/
    Remove a station from favorites.
    """
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'station_id'
    lookup_url_kwarg = 'station_id'

    def get_queryset(self):
        return Favorite.objects.filter(user=self.request.user)

    def destroy(self, request, *args, **kwargs):
        try:
            return super().destroy(request, *args, **kwargs)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_404_NOT_FOUND
            )


# ─── Google Maps Proxy Views ────────────────────────────────────────

class DirectionsProxyView(views.APIView):
    """
    GET /api/directions/?origin_lat=&origin_lng=&dest_lat=&dest_lng=
    Proxy Google Directions API to hide API key from frontend.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        origin_lat = request.query_params.get('origin_lat')
        origin_lng = request.query_params.get('origin_lng')
        dest_lat = request.query_params.get('dest_lat')
        dest_lng = request.query_params.get('dest_lng')

        if not all([origin_lat, origin_lng, dest_lat, dest_lng]):
            return Response(
                {'error': 'origin_lat, origin_lng, dest_lat, dest_lng are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        api_key = settings.GOOGLE_MAPS_API_KEY
        url = (
            f"https://maps.googleapis.com/maps/api/directions/json"
            f"?origin={origin_lat},{origin_lng}"
            f"&destination={dest_lat},{dest_lng}"
            f"&key={api_key}"
            f"&mode=driving"
        )

        try:
            response = http_requests.get(url, timeout=10)
            return Response(response.json())
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PlacesSearchProxyView(views.APIView):
    """
    GET /api/places/search/?query=<query>&lat=<lat>&lng=<lng>
    Proxy Google Places API for station search with autocomplete.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        query = request.query_params.get('query', '')
        lat = request.query_params.get('lat')
        lng = request.query_params.get('lng')

        api_key = settings.GOOGLE_MAPS_API_KEY
        if not api_key:
            return Response(
                {'error': 'Google Maps API key not configured'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
        params = {
            'query': f"CNG station {query}",
            'key': api_key,
        }
        if lat and lng:
            params['location'] = f"{lat},{lng}"
            params['radius'] = settings.STATION_FETCH_RADIUS

        try:
            response = http_requests.get(url, params=params, timeout=10)
            return Response(response.json())
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PlacesAutocompleteProxyView(views.APIView):
    """
    GET /api/places/autocomplete/?input=<text>&lat=<lat>&lng=<lng>
    Proxy Google Places Autocomplete API.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        input_text = request.query_params.get('input', '')
        lat = request.query_params.get('lat')
        lng = request.query_params.get('lng')

        api_key = settings.GOOGLE_MAPS_API_KEY
        if not api_key:
            return Response(
                {'error': 'Google Maps API key not configured'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        url = "https://maps.googleapis.com/maps/api/place/autocomplete/json"
        params = {
            'input': input_text,
            'types': 'establishment',
            'key': api_key,
        }
        if lat and lng:
            params['location'] = f"{lat},{lng}"
            params['radius'] = 50000

        try:
            response = http_requests.get(url, params=params, timeout=10)
            return Response(response.json())
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ─── Heatmap Data ────────────────────────────────────────────────────

class HeatmapDataView(views.APIView):
    """
    GET /api/stations/heatmap/
    Return station locations with queue intensity for heatmap visualization.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        stations = Station.objects.filter(is_active=True)
        data = []
        for station in stations:
            queue_len = station.average_queue_length
            data.append({
                'lat': station.latitude,
                'lng': station.longitude,
                'weight': max(queue_len, 1),  # minimum weight of 1
                'name': station.name,
                'queue': queue_len,
            })
        return Response(data)
