"""
URL configuration for SmartCNG project.
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from django.conf import settings

urlpatterns = [
    path('admin/', admin.site.urls),
    # API endpoints
    path('api/auth/', include('accounts.urls')),
    path('api/', include('stations.urls')),
    path('api/', include('bookings.urls')),
    # Google Maps API key endpoint (proxied)
    path('api/config/', include('smartcng.config_urls')),
    # Frontend pages (catch-all last)
    path('', TemplateView.as_view(template_name='index.html'), name='home'),
    path('login/', TemplateView.as_view(template_name='login.html'), name='login'),
    path('register/', TemplateView.as_view(template_name='register.html'), name='register'),
    path('dashboard/', TemplateView.as_view(template_name='dashboard.html'), name='dashboard'),
    path('station/<int:station_id>/', TemplateView.as_view(template_name='station_detail.html'), name='station_detail'),
    path('bookings/', TemplateView.as_view(template_name='bookings.html'), name='bookings'),
    path('admin-dashboard/', include('control_panel.urls')),
]
