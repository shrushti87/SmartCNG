/**
 * SmartCNG – API Client Module
 * Handles all communication with the Django REST backend.
 */

const API = {
    BASE_URL: '/api',

    // ─── Auth token management ──────────────────────────
    getToken() {
        return localStorage.getItem('smartcng_access_token');
    },

    getRefreshToken() {
        return localStorage.getItem('smartcng_refresh_token');
    },

    setTokens(access, refresh) {
        localStorage.setItem('smartcng_access_token', access);
        localStorage.setItem('smartcng_refresh_token', refresh);
    },

    clearTokens() {
        localStorage.removeItem('smartcng_access_token');
        localStorage.removeItem('smartcng_refresh_token');
        localStorage.removeItem('smartcng_user');
    },

    getUser() {
        const u = localStorage.getItem('smartcng_user');
        return u ? JSON.parse(u) : null;
    },

    setUser(user) {
        localStorage.setItem('smartcng_user', JSON.stringify(user));
    },

    isLoggedIn() {
        return !!this.getToken();
    },

    // ─── Core fetch wrapper ─────────────────────────────
    async request(endpoint, options = {}) {
        const url = `${this.BASE_URL}${endpoint}`;
        const headers = {
            'Content-Type': 'application/json',
            ...options.headers,
        };

        const token = this.getToken();
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        try {
            let response = await fetch(url, {
                ...options,
                headers,
            });

            // If 401, try refreshing the token
            if (response.status === 401 && this.getRefreshToken()) {
                const refreshed = await this.refreshToken();
                if (refreshed) {
                    headers['Authorization'] = `Bearer ${this.getToken()}`;
                    response = await fetch(url, { ...options, headers });
                }
            }

            let data = {};
            if (response.status !== 204) {
                data = await response.json();
            }

            if (!response.ok) {
                throw { status: response.status, data };
            }

            return data;
        } catch (error) {
            if (error.status) throw error;
            console.error('Network error:', error);
            throw { status: 0, data: { error: 'Network error. Please check your connection.' } };
        }
    },

    async refreshToken() {
        try {
            const response = await fetch(`${this.BASE_URL}/auth/token/refresh/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ refresh: this.getRefreshToken() }),
            });

            if (response.ok) {
                const data = await response.json();
                this.setTokens(data.access, data.refresh || this.getRefreshToken());
                return true;
            }
        } catch (e) {
            console.error('Token refresh failed:', e);
        }

        this.clearTokens();
        return false;
    },

    // ─── Auth endpoints ─────────────────────────────────
    async register(data) {
        const result = await this.request('/auth/register/', {
            method: 'POST',
            body: JSON.stringify(data),
        });
        this.setTokens(result.tokens.access, result.tokens.refresh);
        this.setUser(result.user);
        return result;
    },

    async login(username, password) {
        const result = await this.request('/auth/login/', {
            method: 'POST',
            body: JSON.stringify({ username, password }),
        });
        this.setTokens(result.tokens.access, result.tokens.refresh);
        this.setUser(result.user);
        return result;
    },

    async logout() {
        try {
            await this.request('/auth/logout/', { method: 'POST' });
        } catch (e) {
            console.error('Logout error:', e);
        }
        this.clearTokens();
        window.location.href = '/';
    },

    async getProfile() {
        return this.request('/auth/profile/');
    },

    async updateProfile(data) {
        return this.request('/auth/profile/', {
            method: 'PATCH',
            body: JSON.stringify(data),
        });
    },

    // ─── Station endpoints ──────────────────────────────
    async getStations(search = '') {
        const params = search ? `?search=${encodeURIComponent(search)}` : '';
        return this.request(`/stations/${params}`);
    },

    async getStation(id) {
        return this.request(`/stations/${id}/`);
    },

    async getNearbyStations(lat, lng, radius = 25, sort = 'distance') {
        return this.request(
            `/stations/nearby/?lat=${lat}&lng=${lng}&radius=${radius}&sort=${sort}`
        );
    },

    async getBestStation(lat, lng) {
        return this.request(`/stations/best/?lat=${lat}&lng=${lng}`);
    },

    async getHeatmapData() {
        return this.request('/stations/heatmap/');
    },

    // ─── Queue endpoints ────────────────────────────────
    async submitQueueUpdate(data) {
        return this.request('/queue/update/', {
            method: 'POST',
            body: JSON.stringify(data),
        });
    },

    async getLatestQueue(stationId) {
        return this.request(`/queue/latest/${stationId}/`);
    },

    async voteOnUpdate(updateId, voteType) {
        return this.request(`/queue/vote/${updateId}/`, {
            method: 'POST',
            body: JSON.stringify({ vote_type: voteType }),
        });
    },

    // ─── Booking endpoints ──────────────────────────────
    async getSlots(stationId, date) {
        const params = date ? `?date=${date}` : '';
        return this.request(`/slots/${stationId}/${params}`);
    },

    async createBooking(data) {
        return this.request('/booking/create/', {
            method: 'POST',
            body: JSON.stringify(data),
        });
    },

    async getUserBookings() {
        return this.request('/booking/user/');
    },

    async cancelBooking(bookingId) {
        return this.request(`/booking/cancel/${bookingId}/`, {
            method: 'POST',
        });
    },

    // ─── Favorites endpoints ────────────────────────────
    async getFavorites() {
        return this.request('/favorites/');
    },

    async addFavorite(stationId) {
        return this.request('/favorites/', {
            method: 'POST',
            body: JSON.stringify({ station: stationId }),
        });
    },

    async removeFavorite(stationId) {
        return this.request(`/favorites/${stationId}/`, {
            method: 'DELETE',
        });
    },

    // ─── Directions proxy ───────────────────────────────
    async getDirections(originLat, originLng, destLat, destLng) {
        return this.request(
            `/directions/?origin_lat=${originLat}&origin_lng=${originLng}&dest_lat=${destLat}&dest_lng=${destLng}`
        );
    },

    // ─── Places proxy ───────────────────────────────────
    async searchPlaces(query, lat, lng) {
        let params = `?query=${encodeURIComponent(query)}`;
        if (lat && lng) params += `&lat=${lat}&lng=${lng}`;
        return this.request(`/places/search/${params}`);
    },

    async getPlacesAutocomplete(input, lat, lng) {
        let params = `?input=${encodeURIComponent(input)}`;
        if (lat && lng) params += `&lat=${lat}&lng=${lng}`;
        return this.request(`/places/autocomplete/${params}`);
    },

    // ─── Maps config ────────────────────────────────────
    async getMapsConfig() {
        const response = await fetch('/api/config/maps/');
        return response.json();
    },
};
