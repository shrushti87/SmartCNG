"""
Admin configuration for accounts app.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """Custom admin for the User model with additional fields."""
    list_display = ('username', 'email', 'phone', 'vehicle_number', 'vehicle_type', 'is_active', 'date_joined')
    list_filter = ('vehicle_type', 'is_active', 'is_staff', 'date_joined')
    search_fields = ('username', 'email', 'phone', 'vehicle_number')
    fieldsets = UserAdmin.fieldsets + (
        ('Vehicle Info', {'fields': ('phone', 'vehicle_number', 'vehicle_type')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Vehicle Info', {'fields': ('phone', 'vehicle_number', 'vehicle_type')}),
    )
