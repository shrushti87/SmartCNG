from django import forms
from stations.models import Station
from bookings.models import Booking
from django.contrib.auth import get_user_model

User = get_user_model()

class StationForm(forms.ModelForm):
    class Meta:
        model = Station
        fields = [
            'name', 'address', 'latitude', 'longitude', 
            'price_per_kg', 'queue_time', 'status', 'description'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input'}),
            'address': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 3}),
            'latitude': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.000001'}),
            'longitude': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.000001'}),
            'price_per_kg': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01'}),
            'queue_time': forms.NumberInput(attrs={'class': 'form-input'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 3}),
        }

class BookingStatusForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['status']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'})
        }
