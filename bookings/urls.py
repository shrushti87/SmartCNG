"""
URL routing for booking API endpoints.
"""
from django.urls import path
from . import views

urlpatterns = [
    path('slots/<int:station_id>/', views.SlotListView.as_view(), name='slot_list'),
    path('booking/create/', views.BookingCreateView.as_view(), name='booking_create'),
    path('booking/user/', views.UserBookingsView.as_view(), name='booking_user'),
    path('booking/cancel/<uuid:booking_id>/', views.BookingCancelView.as_view(), name='booking_cancel'),
    path('booking/<uuid:booking_id>/', views.BookingDetailView.as_view(), name='booking_detail'),
]
