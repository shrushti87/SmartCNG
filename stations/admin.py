"""
Admin configuration for stations app.
"""
from django.contrib import admin
from .models import Station, QueueUpdate, QueueVote, Favorite


@admin.register(Station)
class StationAdmin(admin.ModelAdmin):
    """Admin for CNG Station management."""
    list_display = ('name', 'address', 'status', 'price_per_kg', 'is_active', 'updated_at')
    list_filter = ('status', 'is_active', 'created_at')
    search_fields = ('name', 'address', 'place_id')
    list_editable = ('status', 'price_per_kg', 'is_active')
    readonly_fields = ('place_id', 'created_at', 'updated_at')
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'address', 'phone', 'place_id')
        }),
        ('Location', {
            'fields': ('latitude', 'longitude')
        }),
        ('Status & Pricing', {
            'fields': ('status', 'price_per_kg', 'is_active')
        }),
        ('Hours', {
            'fields': ('opening_hours',),
            'classes': ('collapse',),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )


@admin.register(QueueUpdate)
class QueueUpdateAdmin(admin.ModelAdmin):
    """Admin for queue/crowd updates."""
    list_display = ('station', 'user', 'queue_length', 'availability', 'upvotes', 'downvotes', 'timestamp')
    list_filter = ('availability', 'timestamp')
    search_fields = ('station__name', 'user__username')
    readonly_fields = ('upvotes', 'downvotes', 'timestamp')


@admin.register(QueueVote)
class QueueVoteAdmin(admin.ModelAdmin):
    """Admin for queue votes."""
    list_display = ('update', 'user', 'vote_type', 'created_at')
    list_filter = ('vote_type', 'created_at')


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    """Admin for user favorites."""
    list_display = ('user', 'station', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'station__name')
