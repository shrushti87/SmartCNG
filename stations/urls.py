"""
URL routing for stations API endpoints.
"""
from django.urls import path
from . import views

urlpatterns = [
    # Stations
    path('stations/', views.StationListView.as_view(), name='station_list'),
    path('stations/<int:pk>/', views.StationDetailView.as_view(), name='station_detail'),
    path('stations/nearby/', views.NearbyStationsView.as_view(), name='stations_nearby'),
    path('stations/best/', views.BestStationView.as_view(), name='station_best'),
    path('stations/heatmap/', views.HeatmapDataView.as_view(), name='stations_heatmap'),

    # Queue updates
    path('queue/update/', views.QueueUpdateCreateView.as_view(), name='queue_update_create'),
    path('queue/latest/<int:station_id>/', views.QueueUpdateLatestView.as_view(), name='queue_latest'),
    path('queue/vote/<int:update_id>/', views.QueueVoteView.as_view(), name='queue_vote'),

    # Favorites
    path('favorites/', views.FavoriteListCreateView.as_view(), name='favorites_list_create'),
    path('favorites/<int:station_id>/', views.FavoriteDeleteView.as_view(), name='favorites_delete'),

    # Google Maps proxies
    path('directions/', views.DirectionsProxyView.as_view(), name='directions_proxy'),
    path('places/search/', views.PlacesSearchProxyView.as_view(), name='places_search'),
    path('places/autocomplete/', views.PlacesAutocompleteProxyView.as_view(), name='places_autocomplete'),
]
