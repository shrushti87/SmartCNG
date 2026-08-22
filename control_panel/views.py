import uuid
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from stations.models import Station
from bookings.models import Booking
from django.contrib.auth import get_user_model
from django.db.models import Count
from .forms import StationForm, BookingStatusForm

User = get_user_model()

def is_admin(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)

@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    total_stations = Station.objects.count()
    total_bookings = Booking.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    
    context = {
        'total_stations': total_stations,
        'total_bookings': total_bookings,
        'active_users': active_users,
    }
    return render(request, 'control_panel/admin_dashboard.html', context)

# --- Stations ---
@login_required
@user_passes_test(is_admin)
def station_list(request):
    stations = Station.objects.all().order_by('-created_at')
    return render(request, 'control_panel/station_list.html', {'stations': stations})

@login_required
@user_passes_test(is_admin)
def station_add(request):
    if request.method == 'POST':
        form = StationForm(request.POST)
        if form.is_valid():
            station = form.save(commit=False)
            # provide a placeholder place_id since it's required in the model
            station.place_id = f"custom_station_{uuid.uuid4().hex[:12]}"
            station.save()
            messages.success(request, 'Station added successfully.')
            return redirect('admin_station_list')
    else:
        form = StationForm()
    return render(request, 'control_panel/station_form.html', {'form': form, 'title': 'Add Station'})

@login_required
@user_passes_test(is_admin)
def station_edit(request, station_id):
    station = get_object_or_404(Station, id=station_id)
    if request.method == 'POST':
        form = StationForm(request.POST, instance=station)
        if form.is_valid():
            form.save()
            messages.success(request, 'Station updated successfully.')
            return redirect('admin_station_list')
    else:
        form = StationForm(instance=station)
    return render(request, 'control_panel/station_form.html', {'form': form, 'title': f'Edit Station: {station.name}'})

@login_required
@user_passes_test(is_admin)
def station_delete(request, station_id):
    station = get_object_or_404(Station, id=station_id)
    if request.method == 'POST':
        station.delete()
        messages.success(request, 'Station deleted successfully.')
        return redirect('admin_station_list')
    return render(request, 'control_panel/station_confirm_delete.html', {'station': station})

# --- Bookings ---
@login_required
@user_passes_test(is_admin)
def booking_list(request, station_id=None):
    if station_id:
        station = get_object_or_404(Station, id=station_id)
        bookings = Booking.objects.filter(station=station).order_by('-created_at')
        title = f'Bookings for {station.name}'
    else:
        bookings = Booking.objects.all().order_by('-created_at')
        title = 'All Bookings'
        
    if request.method == 'POST':
        booking_id = request.POST.get('booking_id')
        new_status = request.POST.get('status')
        booking = get_object_or_404(Booking, id=booking_id)
        if new_status in dict(Booking.STATUS_CHOICES):
            booking.status = new_status
            booking.save()
            messages.success(request, f'Booking {booking.token} status updated to {new_status}.')
        return redirect(request.path)
            
    return render(request, 'control_panel/booking_list.html', {
        'bookings': bookings, 
        'title': title,
        'status_choices': Booking.STATUS_CHOICES
    })

# --- Users ---
@login_required
@user_passes_test(is_admin)
def user_list(request):
    users = User.objects.annotate(booking_count=Count('bookings')).all().order_by('-date_joined')
    return render(request, 'control_panel/user_list.html', {'users': users})

@login_required
@user_passes_test(is_admin)
def user_toggle_status(request, user_id):
    user_obj = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        user_obj.is_active = not user_obj.is_active
        user_obj.save()
        status = "activated" if user_obj.is_active else "deactivated"
        messages.success(request, f'User {user_obj.username} {status}.')
    return redirect('admin_user_list')

@login_required
@user_passes_test(is_admin)
def user_delete(request, user_id):
    user_obj = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        # Don't let admin delete themselves
        if user_obj != request.user:
            user_obj.delete()
            messages.success(request, 'User deleted successfully.')
        else:
            messages.error(request, 'You cannot delete yourself.')
        return redirect('admin_user_list')
    return render(request, 'control_panel/user_confirm_delete.html', {'user_obj': user_obj})

@login_required
@user_passes_test(is_admin)
def user_history(request, user_id):
    user_obj = get_object_or_404(User, id=user_id)
    bookings = Booking.objects.filter(user=user_obj).order_by('-created_at')
    return render(request, 'control_panel/user_booking_history.html', {'user_obj': user_obj, 'bookings': bookings})
