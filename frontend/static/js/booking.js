/**
 * SmartCNG – Booking UI Module
 * Handles booking modal, slot selection, and booking management.
 */

const BookingUI = {
    selectedStationId: null,
    selectedStationName: '',
    selectedSlotId: null,
    selectedDate: null,

    // ─── Open Booking Modal ─────────────────────────────
    openBookingModal(stationId, stationName) {
        if (!API.isLoggedIn()) {
            Utils.showToast('Please login to book a slot', 'error');
            setTimeout(() => window.location.href = '/login/', 1500);
            return;
        }

        this.selectedStationId = stationId;
        this.selectedStationName = stationName;
        this.selectedSlotId = null;

        const modal = document.getElementById('booking-modal');
        if (!modal) return;

        modal.querySelector('.booking-station-name').textContent = stationName;

        // Set default date to today
        const dateInput = modal.querySelector('#booking-date');
        const today = new Date().toISOString().split('T')[0];
        dateInput.value = today;
        dateInput.min = today;

        this.selectedDate = today;

        Utils.openModal('booking-modal');
        this.loadSlots();
    },

    // ─── Load Available Slots ───────────────────────────
    async loadSlots() {
        const slotsContainer = document.getElementById('slots-grid');
        if (!slotsContainer) return;

        slotsContainer.innerHTML = `
            <div class="loading-overlay">
                <div class="loading-spinner"></div>
                <span style="margin-left: 8px;">Loading slots...</span>
            </div>
        `;

        try {
            const data = await API.getSlots(this.selectedStationId, this.selectedDate);
            const slots = data.results || data || [];

            if (slots.length === 0) {
                slotsContainer.innerHTML = `
                    <div class="empty-state" style="padding: 20px;">
                        <div class="empty-icon">📅</div>
                        <h3>No slots available</h3>
                        <p>No time slots configured for this station.</p>
                    </div>
                `;
                return;
            }

            slotsContainer.innerHTML = slots.map(slot => {
                const isFull = slot.available_capacity <= 0;
                return `
                    <div class="slot-item ${isFull ? 'full' : ''} ${this.selectedSlotId === slot.id ? 'selected' : ''}"
                         data-slot-id="${slot.id}"
                         onclick="${isFull ? '' : `BookingUI.selectSlot(${slot.id})`}">
                        <div class="slot-time">${this.formatSlotTime(slot.start_time)} - ${this.formatSlotTime(slot.end_time)}</div>
                        <div class="slot-capacity">${isFull ? 'Full' : `${slot.available_capacity} left`}</div>
                    </div>
                `;
            }).join('');
        } catch (error) {
            console.error('Failed to load slots:', error);
            slotsContainer.innerHTML = `
                <div class="empty-state" style="padding: 20px;">
                    <p>Failed to load slots. Please try again.</p>
                </div>
            `;
        }
    },

    // ─── Select Slot ────────────────────────────────────
    selectSlot(slotId) {
        this.selectedSlotId = slotId;

        // Update UI
        document.querySelectorAll('.slot-item').forEach(item => {
            item.classList.remove('selected');
        });
        const selected = document.querySelector(`.slot-item[data-slot-id="${slotId}"]`);
        if (selected) {
            selected.classList.add('selected');
        }
    },

    // ─── Confirm Booking ────────────────────────────────
    async confirmBooking() {
        if (!this.selectedSlotId) {
            Utils.showToast('Please select a time slot', 'error');
            return;
        }

        const vehicleNumber = document.getElementById('booking-vehicle')?.value || '';
        if (!vehicleNumber.trim()) {
            Utils.showToast('Vehicle number is required', 'error');
            return;
        }
        const notes = document.getElementById('booking-notes')?.value || '';

        const confirmBtn = document.getElementById('confirm-booking-btn');
        if (confirmBtn) {
            confirmBtn.disabled = true;
            confirmBtn.innerHTML = '<div class="loading-spinner"></div> Booking...';
        }

        try {
            const result = await API.createBooking({
                station: this.selectedStationId,
                slot: this.selectedSlotId,
                date: this.selectedDate,
                vehicle_number: vehicleNumber,
                notes: notes,
            });

            Utils.closeModal('booking-modal');
            Utils.showToast(
                `Booking confirmed! Token: ${result.booking.token}`,
                'success',
                6000
            );

            // Show booking confirmation
            this.showBookingConfirmation(result.booking);
        } catch (error) {
            const msg = error.data
                ? (typeof error.data === 'object'
                    ? Object.values(error.data).flat().join(', ')
                    : error.data.error || 'Booking failed')
                : 'Booking failed. Please try again.';
            Utils.showToast(msg, 'error');
        } finally {
            if (confirmBtn) {
                confirmBtn.disabled = false;
                confirmBtn.innerHTML = '✓ Confirm Booking';
            }
        }
    },

    // ─── Show Booking Confirmation ──────────────────────
    showBookingConfirmation(booking) {
        const modal = document.getElementById('confirmation-modal');
        if (!modal) return;

        modal.querySelector('.conf-token').textContent = booking.token;
        modal.querySelector('.conf-station').textContent = booking.station_name;
        modal.querySelector('.conf-date').textContent = Utils.formatDate(booking.date);
        modal.querySelector('.conf-slot').textContent = booking.slot_time;
        modal.querySelector('.conf-status').textContent = booking.status;

        Utils.openModal('confirmation-modal');
    },

    // ─── Date Change Handler ────────────────────────────
    onDateChange(dateValue) {
        this.selectedDate = dateValue;
        this.selectedSlotId = null;
        this.loadSlots();
    },

    // ─── Load User Bookings ─────────────────────────────
    async loadUserBookings() {
        const container = document.getElementById('bookings-list');
        if (!container) return;

        container.innerHTML = `
            <div class="loading-overlay">
                <div class="loading-spinner"></div>
                <span style="margin-left: 8px;">Loading bookings...</span>
            </div>
        `;

        try {
            const data = await API.getUserBookings();
            const bookings = data.results || data || [];

            if (bookings.length === 0) {
                container.innerHTML = `
                    <div class="empty-state">
                        <div class="empty-icon">📋</div>
                        <h3>No bookings yet</h3>
                        <p>Find a station and book a slot to get started.</p>
                        <a href="/" class="btn btn-primary" style="margin-top: 16px;">Find Stations</a>
                    </div>
                `;
                return;
            }

            container.innerHTML = bookings.map(b => `
                <div class="booking-item">
                    <div class="booking-info">
                        <div class="booking-station">${b.station_name}</div>
                        <div class="booking-details">
                            📅 ${Utils.formatDate(b.date)} · ⏰ ${b.slot_time} · 🚗 ${b.vehicle_number || 'N/A'}
                        </div>
                    </div>
                    <div style="display: flex; align-items: center; gap: 12px;">
                        <span class="booking-token">${b.token}</span>
                        <span class="booking-status ${b.status}">${b.status}</span>
                        ${b.status === 'confirmed' || b.status === 'pending' ? `
                            <button class="btn btn-danger btn-sm" onclick="BookingUI.cancelBooking('${b.booking_id}')">
                                Cancel
                            </button>
                        ` : ''}
                    </div>
                </div>
            `).join('');
        } catch (error) {
            console.error('Failed to load bookings:', error);
            container.innerHTML = `<p style="text-align: center; color: var(--color-text-muted);">Failed to load bookings.</p>`;
        }
    },

    // ─── Cancel Booking ─────────────────────────────────
    async cancelBooking(bookingId) {
        if (!confirm('Are you sure you want to cancel this booking?')) return;

        try {
            await API.cancelBooking(bookingId);
            Utils.showToast('Booking cancelled', 'success');
            this.loadUserBookings();
        } catch (error) {
            Utils.showToast('Failed to cancel booking', 'error');
        }
    },

    // ─── Format Slot Time ───────────────────────────────
    formatSlotTime(timeStr) {
        if (!timeStr) return '';
        const parts = timeStr.split(':');
        const h = parseInt(parts[0]);
        const m = parts[1];
        const ampm = h >= 12 ? 'PM' : 'AM';
        const h12 = h % 12 || 12;
        return `${h12}:${m} ${ampm}`;
    },
};
