"""
Config API - Proxies the Google Maps API key to frontend.
"""
from django.urls import path
from django.http import JsonResponse
from django.conf import settings


def get_maps_config(request):
    """Return Google Maps API key for frontend use."""
    return JsonResponse({
        'google_maps_api_key': settings.GOOGLE_MAPS_API_KEY,
    })


urlpatterns = [
    path('maps/', get_maps_config, name='maps_config'),
]
