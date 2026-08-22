from django.urls import path
from . import views

urlpatterns = [
    path('', views.admin_dashboard, name='admin_dashboard'),
    
    # Stations
    path('stations/', views.station_list, name='admin_station_list'),
    path('stations/add/', views.station_add, name='admin_station_add'),
    path('stations/edit/<int:station_id>/', views.station_edit, name='admin_station_edit'),
    path('stations/delete/<int:station_id>/', views.station_delete, name='admin_station_delete'),
    
    # Bookings
    path('bookings/', views.booking_list, name='admin_booking_list'),
    path('bookings/<int:station_id>/', views.booking_list, name='admin_station_bookings'),
    
    # Users
    path('users/', views.user_list, name='admin_user_list'),
    path('users/toggle/<int:user_id>/', views.user_toggle_status, name='admin_user_toggle'),
    path('users/delete/<int:user_id>/', views.user_delete, name='admin_user_delete'),
    path('users/history/<int:user_id>/', views.user_history, name='admin_user_history'),
]
