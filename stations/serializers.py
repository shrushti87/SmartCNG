"""
Serializers for stations, queue updates, favorites.
"""
from rest_framework import serializers
from .models import Station, QueueUpdate, QueueVote, Favorite


class StationSerializer(serializers.ModelSerializer):
    """Full station serializer with computed fields."""
    latest_queue_length = serializers.SerializerMethodField()
    latest_availability = serializers.SerializerMethodField()
    distance = serializers.FloatField(read_only=True, required=False)
    is_favorite = serializers.SerializerMethodField()

    class Meta:
        model = Station
        fields = (
            'id', 'name', 'address', 'latitude', 'longitude', 'place_id',
            'price_per_kg', 'status', 'phone', 'opening_hours',
            'is_active', 'latest_queue_length', 'latest_availability',
            'distance', 'is_favorite', 'created_at', 'updated_at'
        )

    def get_latest_queue_length(self, obj):
        """Get latest queue length from non-expired updates."""
        latest = obj.latest_queue
        return latest.queue_length if latest else None

    def get_latest_availability(self, obj):
        """Get latest availability status from non-expired updates."""
        latest = obj.latest_queue
        return latest.availability if latest else obj.status

    def get_is_favorite(self, obj):
        """Check if the current user has favorited this station."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Favorite.objects.filter(
                user=request.user, station=obj
            ).exists()
        return False


class StationListSerializer(serializers.ModelSerializer):
    """Lightweight station serializer for list views."""
    latest_queue_length = serializers.SerializerMethodField()
    latest_availability = serializers.SerializerMethodField()
    distance = serializers.FloatField(read_only=True, required=False)

    class Meta:
        model = Station
        fields = (
            'id', 'name', 'address', 'latitude', 'longitude',
            'status', 'latest_queue_length',
            'latest_availability', 'distance'
        )

    def get_latest_queue_length(self, obj):
        latest = obj.latest_queue
        return latest.queue_length if latest else None

    def get_latest_availability(self, obj):
        latest = obj.latest_queue
        return latest.availability if latest else obj.status


class QueueUpdateSerializer(serializers.ModelSerializer):
    """Serializer for queue/crowd updates."""
    username = serializers.CharField(source='user.username', read_only=True)
    reliability_score = serializers.IntegerField(read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    user_vote = serializers.SerializerMethodField()

    class Meta:
        model = QueueUpdate
        fields = (
            'id', 'station', 'username', 'queue_length', 'availability',
            'comment', 'upvotes', 'downvotes', 'reliability_score',
            'is_expired', 'user_vote', 'timestamp'
        )
        read_only_fields = ('id', 'upvotes', 'downvotes', 'timestamp')

    def get_user_vote(self, obj):
        """Get current user's vote on this update."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            vote = QueueVote.objects.filter(
                update=obj, user=request.user
            ).first()
            return vote.vote_type if vote else None
        return None


class QueueUpdateCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating queue updates."""
    class Meta:
        model = QueueUpdate
        fields = ('station', 'queue_length', 'availability', 'comment')

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class QueueVoteSerializer(serializers.Serializer):
    """Serializer for voting on queue updates."""
    vote_type = serializers.ChoiceField(choices=['up', 'down'])


class FavoriteSerializer(serializers.ModelSerializer):
    """Serializer for user favorites."""
    station_name = serializers.CharField(source='station.name', read_only=True)
    station_address = serializers.CharField(source='station.address', read_only=True)

    class Meta:
        model = Favorite
        fields = ('id', 'station', 'station_name', 'station_address', 'created_at')
        read_only_fields = ('id', 'created_at')

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)
