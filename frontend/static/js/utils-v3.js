/**
 * SmartCNG – Utility Functions
 * Shared helpers for UI, formatting, geolocation, etc.
 */

const Utils = {
    // ─── Geolocation ────────────────────────────────────
    getCurrentPosition() {
        return new Promise((resolve, reject) => {
            if (!navigator.geolocation) {
                reject(new Error('Geolocation not supported'));
                return;
            }
            navigator.geolocation.getCurrentPosition(
                (pos) => resolve({
                    lat: pos.coords.latitude,
                    lng: pos.coords.longitude,
                }),
                (err) => reject(err),
                { enableHighAccuracy: true, timeout: 10000 }
            );
        });
    },

    // ─── Haversine Distance (km) ────────────────────────
    haversineDistance(lat1, lon1, lat2, lon2) {
        const R = 6371;
        const dLat = this.toRad(lat2 - lat1);
        const dLon = this.toRad(lon2 - lon1);
        const a = Math.sin(dLat / 2) ** 2 +
            Math.cos(this.toRad(lat1)) *
            Math.cos(this.toRad(lat2)) *
            Math.sin(dLon / 2) ** 2;
        const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
        return (R * c).toFixed(1);
    },

    toRad(deg) {
        return deg * (Math.PI / 180);
    },

    // ─── Formatting ─────────────────────────────────────
    formatDistance(km) {
        km = parseFloat(km);
        if (km < 1) return `${Math.round(km * 1000)} m`;
        return `${km.toFixed(1)} km`;
    },

    formatTime(minutes) {
        if (minutes < 60) return `${Math.round(minutes)} min`;
        const hrs = Math.floor(minutes / 60);
        const mins = Math.round(minutes % 60);
        return `${hrs}h ${mins}m`;
    },

    formatTimeAgo(timestamp) {
        const now = new Date();
        const date = new Date(timestamp);
        const diff = Math.floor((now - date) / 1000);

        if (diff < 60) return 'just now';
        if (diff < 3600) return `${Math.floor(diff / 60)} min ago`;
        if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
        return date.toLocaleDateString();
    },

    formatDate(dateStr) {
        const d = new Date(dateStr);
        return d.toLocaleDateString('en-IN', {
            weekday: 'short',
            day: 'numeric',
            month: 'short',
            year: 'numeric',
        });
    },

    // ─── Status Helpers ─────────────────────────────────
    getStatusColor(status) {
        const colors = {
            available: '#22c55e',
            low: '#f59e0b',
            no_gas: '#ef4444',
            closed: '#6b7280',
        };
        return colors[status] || colors.closed;
    },

    getStatusLabel(status) {
        const labels = {
            available: 'Available',
            low: 'Low Gas',
            no_gas: 'No Gas',
            closed: 'Closed',
        };
        return labels[status] || 'Unknown';
    },

    getStatusEmoji(status) {
        const emojis = {
            available: '🟢',
            low: '🟡',
            no_gas: '🔴',
            closed: '⚫',
        };
        return emojis[status] || '⚪';
    },

    // ─── Toast Notifications ────────────────────────────
    showToast(message, type = 'info', duration = 4000) {
        let container = document.querySelector('.toast-container');
        if (!container) {
            container = document.createElement('div');
            container.className = 'toast-container';
            document.body.appendChild(container);
        }

        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.innerHTML = `
            <span class="toast-icon">${type === 'success' ? '✓' : type === 'error' ? '✕' : 'ℹ'}</span>
            <span class="toast-message">${message}</span>
            <button class="toast-close" onclick="this.parentElement.remove()">×</button>
        `;

        container.appendChild(toast);

        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateX(100px)';
            setTimeout(() => toast.remove(), 300);
        }, duration);
    },

    // ─── Modal Helpers ──────────────────────────────────
    openModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.add('active');
            document.body.style.overflow = 'hidden';
        }
    },

    closeModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.remove('active');
            document.body.style.overflow = '';
        }
    },

    closeAllModals() {
        document.querySelectorAll('.modal-overlay.active').forEach(m => {
            m.classList.remove('active');
        });
        document.body.style.overflow = '';
    },

    // ─── Navbar Auth UI ─────────────────────────────────
    updateNavAuth() {
        const navAuth = document.querySelector('.nav-auth');
        if (!navAuth) return;

        if (API.isLoggedIn()) {
            const user = API.getUser();
            const initial = user ? user.username.charAt(0).toUpperCase() : '?';
            navAuth.innerHTML = `
                <div class="nav-user-info">
                    <div class="user-avatar">${initial}</div>
                    <span>${user ? user.username : 'User'}</span>
                </div>
                <div class="btn-group">
                    <button class="btn btn-outline btn-sm" onclick="API.logout()">Logout</button>
                </div>
            `;
        } else {
            navAuth.innerHTML = `
                <div class="btn-group">
                    <a href="/login/" class="btn btn-secondary btn-sm">Login</a>
                    <a href="/register/" class="btn btn-primary btn-sm">Sign Up</a>
                </div>
            `;
        }
    },

    // ─── Debounce ───────────────────────────────────────
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    // ─── Scroll-aware Navbar ────────────────────────────
    initNavbarScroll() {
        const navbar = document.querySelector('.navbar');
        if (!navbar) return;

        window.addEventListener('scroll', () => {
            if (window.scrollY > 20) {
                navbar.classList.add('scrolled');
            } else {
                navbar.classList.remove('scrolled');
            }
        });
    },

    // ─── Build Station Card HTML ────────────────────────
    buildStationCard(station, userLocation = null) {
        const status = station.latest_availability || station.status || 'available';
        const distance = station.distance != null
            ? this.formatDistance(station.distance)
            : userLocation
                ? this.formatDistance(this.haversineDistance(userLocation.lat, userLocation.lng, station.latitude, station.longitude))
                : '';

        const queueText = station.latest_queue_length != null
            ? `${station.latest_queue_length} vehicles`
            : 'No data';

        return `
            <div class="station-card status-${status}" data-station-id="${station.id}"
                 data-lat="${station.latitude}" data-lng="${station.longitude}">
                <span class="status-badge ${status}">${this.getStatusLabel(status)}</span>
                <div class="station-name">${station.name}</div>
                <div class="station-address">${station.address}</div>
                <div class="station-meta">
                    ${distance ? `<div class="station-meta-item"><span class="icon">📍</span>${distance}</div>` : ''}
                    <div class="station-meta-item"><span class="icon">🚗</span>${queueText}</div>
                    ${station.rating ? `<div class="station-meta-item"><span class="icon">⭐</span>${station.rating}</div>` : ''}
                </div>
                <div class="station-actions btn-group">
                    <button class="btn btn-primary btn-sm" onclick="event.stopPropagation(); SmartMap.showDirections(${station.latitude}, ${station.longitude}, '${station.name.replace(/'/g, "\\'")}')">
                        🧭 Directions
                    </button>
                    <button class="btn btn-secondary btn-sm" onclick="event.stopPropagation(); BookingUI.openBookingModal(${station.id}, '${station.name.replace(/'/g, "\\'")}')">
                        📅 Book Slot
                    </button>
                    <button class="btn btn-outline btn-sm" onclick="event.stopPropagation(); window.location.href='/station/${station.id}/'">
                        ℹ️ Details
                    </button>
                </div>
            </div>
        `;
    },
};

// Initialize on load
document.addEventListener('DOMContentLoaded', () => {
    Utils.updateNavAuth();
    Utils.initNavbarScroll();
});
