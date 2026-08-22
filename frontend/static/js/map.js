/**
 * SmartCNG – Leaflet Maps Integration Module
 * Handles map rendering, markers, directions, and heatmap.
 */

const SmartMap = {
    map: null,
    markers: [],
    userMarker: null,
    directionsControl: null,
    heatmapLayer: null,
    userLocation: null,

    // ─── Initialize Map ─────────────────────────────────
    async init(elementId = 'map') {
        const mapElement = document.getElementById(elementId);
        if (!mapElement) return;

        // Default center: Nashik
        const defaultCenter = [20.0110, 73.7903];

        this.map = L.map(elementId, {
            zoomControl: false // We will add it to a specific position if needed, or leave default
        }).setView(defaultCenter, 13);

        L.control.zoom({ position: 'bottomright' }).addTo(this.map);

        // // Add OpenStreetMap tiles
        // L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        //     attribution: '&copy; OpenStreetMap contributors'
        // }).addTo(this.map);

        L.tileLayer('https://{s}.tile.openstreetmap.fr/hot/{z}/{x}/{y}.png', {
            attribution: '&copy; OpenStreetMap contributors'
        }).addTo(this.map);


        // Try to get user location
        try {
            this.userLocation = await Utils.getCurrentPosition();
            this.map.setView([this.userLocation.lat, this.userLocation.lng], 13);
            this.addUserMarker(this.userLocation);
        } catch (e) {
            console.log('Location access denied, using default center');
        }

        // Load stations
        await this.loadStations();
    },

    // ─── Add User Location Marker ───────────────────────
    addUserMarker(position) {
        if (this.userMarker) {
            this.map.removeLayer(this.userMarker);
        }

        const userIcon = L.divIcon({
            className: 'user-marker-icon',
            html: `<div style="background-color: var(--color-accent); width: 16px; height: 16px; border-radius: 50%; border: 3px solid white; box-shadow: 0 0 0 2px var(--color-accent), 0 0 10px rgba(0, 123, 255, 0.5);"></div>`,
            iconSize: [22, 22],
            iconAnchor: [11, 11]
        });

        this.userMarker = L.marker([position.lat, position.lng], {
            icon: userIcon,
            zIndexOffset: 1000
        }).addTo(this.map).bindTooltip("Your Location");

        // Pulsing circle
        L.circle([position.lat, position.lng], {
            color: 'var(--color-accent)',
            fillColor: 'var(--color-accent)',
            fillOpacity: 0.15,
            radius: 100,
            weight: 1
        }).addTo(this.map);
    },

    // ─── Load and Display Stations ──────────────────────
    async loadStations(sort = 'distance') {
        try {
            let data;
            if (this.userLocation) {
                data = await API.getNearbyStations(
                    this.userLocation.lat,
                    this.userLocation.lng,
                    50, // 50km radius
                    sort
                );
                this.displayStations(data.stations || []);
            } else {
                data = await API.getStations();
                this.displayStations(data.results || data || []);
            }
        } catch (error) {
            console.error('Failed to load stations:', error);
            Utils.showToast('Failed to load stations', 'error');
        }
    },

    // ─── Display Stations on Map & List ─────────────────
    displayStations(stations) {
        // Clear existing markers
        this.clearMarkers();

        // Update station list sidebar
        const sidebar = document.getElementById('stations-list');
        if (sidebar) {
            if (stations.length === 0) {
                sidebar.innerHTML = `
                    <div class="empty-state">
                        <div class="empty-icon">⛽</div>
                        <h3>No stations found</h3>
                        <p>Try expanding your search radius</p>
                    </div>
                `;
            } else {
                sidebar.innerHTML = stations.map(s =>
                    Utils.buildStationCard(s, this.userLocation)
                ).join('');

                // Add click handlers to cards
                sidebar.querySelectorAll('.station-card').forEach(card => {
                    card.addEventListener('click', () => {
                        const lat = parseFloat(card.dataset.lat);
                        const lng = parseFloat(card.dataset.lng);
                        this.map.panTo([lat, lng]);
                        // Find and trigger marker popup
                        const marker = this.markers.find(m =>
                            m.stationData.id == card.dataset.stationId
                        );
                        if (marker) {
                            marker.openPopup();
                        }
                    });
                });
            }
        }

        // Update stats
        this.updateStats(stations);

        // Add markers to map
        stations.forEach(station => this.addStationMarker(station));

        // Load best station recommendation
        this.loadBestStation();
    },

    // ─── Add Station Marker ─────────────────────────────
    addStationMarker(station) {
        const status = station.latest_availability || station.status || 'available';
        const markerColor = Utils.getStatusColor(status);

        const svgIcon = L.divIcon({
            className: 'custom-div-icon',
            html: `<svg width="24" height="36" viewBox="0 0 24 36" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z" fill="${markerColor}" stroke="#ffffff" stroke-width="1"/>
            </svg>`,
            iconSize: [24, 36],
            iconAnchor: [12, 36],
            popupAnchor: [0, -36]
        });

        const marker = L.marker([station.latitude, station.longitude], {
            icon: svgIcon,
            title: station.name
        }).addTo(this.map);

        marker.stationData = station;

        const distance = station.distance != null
            ? Utils.formatDistance(station.distance)
            : this.userLocation
                ? Utils.formatDistance(Utils.haversineDistance(
                    this.userLocation.lat, this.userLocation.lng,
                    station.latitude, station.longitude
                ))
                : '';

        const queueText = station.latest_queue_length != null
            ? `${station.latest_queue_length} vehicles in queue`
            : 'No queue data';

        const user = API.getUser();
        const isAdmin = user && (user.is_staff || user.is_superuser);

        const popupContent = `
            <div class="info-window" style="min-width: 200px;">
                <h3 style="margin: 0 0 5px 0;">${station.name}</h3>
                <p style="margin: 0 0 5px 0; color: #555; font-size: 0.9em;">${station.address}</p>
                <p style="margin: 0 0 5px 0;">${Utils.getStatusEmoji(status)} ${Utils.getStatusLabel(status)} · ${distance ? `📍 ${distance}` : ''}</p>
                <p style="margin: 0 0 10px 0;">🚗 ${queueText}</p>
                <div class="info-actions" style="display: flex; flex-direction: column; gap: 5px;">
                    <button class="btn btn-primary btn-sm"
                        onclick="SmartMap.showDirections(${station.latitude}, ${station.longitude}, '${station.name.replace(/'/g, "\\'")}')">
                        🧭 Directions
                    </button>
                    ${!isAdmin ? `
                    <button class="btn btn-secondary btn-sm"
                        onclick="BookingUI.openBookingModal(${station.id}, '${station.name.replace(/'/g, "\\'")}')">
                        📅 Book
                    </button>
                    ` : ''}
                    <button class="btn btn-outline btn-sm"
                        onclick="window.location.href='/station/${station.id}/'">
                        ℹ Details
                    </button>
                </div>
            </div>
        `;

        marker.bindPopup(popupContent, { maxWidth: 300 });
        this.markers.push(marker);
    },

    // ─── Clear Markers ──────────────────────────────────
    clearMarkers() {
        this.markers.forEach(m => this.map.removeLayer(m));
        this.markers = [];
    },

    // ─── Show Directions ────────────────────────────────
    async showDirections(destLat, destLng, stationName) {
        if (!this.userLocation) {
            Utils.showToast('Location access required for directions', 'error');
            try {
                this.userLocation = await Utils.getCurrentPosition();
            } catch (e) {
                return;
            }
        }

        const panel = document.getElementById('directions-panel');
        if (panel) {
            panel.classList.add('active');
            panel.querySelector('.directions-station-name').textContent = stationName || 'Station';
        }

        this.clearDirections();

        this.directionsControl = L.Routing.control({
            waypoints: [
                L.latLng(this.userLocation.lat, this.userLocation.lng),
                L.latLng(destLat, destLng)
            ],
            routeWhileDragging: false,
            addWaypoints: false,
            showAlternatives: false,
            fitSelectedRoutes: true,
            lineOptions: {
                styles: [{ color: '#007bff', opacity: 0.8, weight: 6 }]
            },
            createMarker: function () { return null; } // don't draw extra markers
        }).addTo(this.map);

        this.directionsControl.on('routesfound', (e) => {
            const routes = e.routes;
            if (routes.length > 0) {
                const summary = routes[0].summary;
                if (panel) {
                    panel.querySelector('.dir-distance').textContent = Utils.formatDistance(summary.totalDistance / 1000);
                    panel.querySelector('.dir-duration').textContent = Math.round(summary.totalTime / 60) + ' min';
                }
            }
        });

        // Also update external link (OSM routing)
        const gmapsLink = document.getElementById('gmaps-link');
        if (gmapsLink) {
            gmapsLink.href = `https://www.openstreetmap.org/directions?engine=osrm_car&route=${this.userLocation.lat},${this.userLocation.lng};${destLat},${destLng}`;
        }
    },

    // ─── Clear Directions ───────────────────────────────
    clearDirections() {
        if (this.directionsControl) {
            this.map.removeControl(this.directionsControl);
            this.directionsControl = null;
        }
        const panel = document.getElementById('directions-panel');
        if (panel) {
            panel.classList.remove('active');
        }
    },

    // ─── Toggle Heatmap ─────────────────────────────────
    async toggleHeatmap() {
        if (this.heatmapLayer) {
            this.map.removeLayer(this.heatmapLayer);
            this.heatmapLayer = null;
            return;
        }

        try {
            const data = await API.getHeatmapData();
            const heatmapData = data.map(item => [item.lat, item.lng, item.weight * 0.5]); // weight scaled for leaflet

            // Assuming leaflet-heat is included
            this.heatmapLayer = L.heatLayer(heatmapData, {
                radius: 25,
                blur: 15,
                maxZoom: 15,
                gradient: {
                    0.2: 'green',
                    0.5: 'yellow',
                    0.7: 'orange',
                    1.0: 'red'
                }
            }).addTo(this.map);
        } catch (error) {
            console.error('Heatmap error:', error);
            Utils.showToast('Failed to load heatmap data', 'error');
        }
    },

    // ─── Update Stats ───────────────────────────────────
    updateStats(stations) {
        const totalEl = document.getElementById('stat-total');
        const availableEl = document.getElementById('stat-available');
        const lowEl = document.getElementById('stat-low');
        const noGasEl = document.getElementById('stat-nogas');

        if (totalEl) totalEl.textContent = stations.length;
        if (availableEl) {
            availableEl.textContent = stations.filter(s =>
                (s.latest_availability || s.status) === 'available'
            ).length;
        }
        if (lowEl) {
            lowEl.textContent = stations.filter(s =>
                (s.latest_availability || s.status) === 'low'
            ).length;
        }
        if (noGasEl) {
            noGasEl.textContent = stations.filter(s =>
                (s.latest_availability || s.status) === 'no_gas'
            ).length;
        }
    },

    // ─── Load Best Station Recommendation ───────────────
    async loadBestStation() {
        if (!this.userLocation) return;

        try {
            const data = await API.getBestStation(
                this.userLocation.lat, this.userLocation.lng
            );

            const banner = document.getElementById('recommendation-banner');
            if (banner && data.name) {
                const distance = data.distance ? Utils.formatDistance(data.distance) : '';
                banner.querySelector('.rec-name').textContent = data.name;
                banner.querySelector('.rec-info').textContent =
                    `${distance} away · ${Utils.getStatusLabel(data.latest_availability || data.status)} · Score: ${data.smart_score || 'N/A'}`;
                banner.style.display = 'flex';
                banner.onclick = () => {
                    this.map.panTo([data.latitude, data.longitude]);

                    // Pop up best station
                    const marker = this.markers.find(m => m.stationData.id == data.id);
                    if (marker) {
                        marker.openPopup();
                    }
                };
            }
        } catch (error) {
            console.log('No best station recommendation available');
        }
    },

    // ─── Search Stations ────────────────────────────────
    async searchStations(query) {
        if (!query.trim()) {
            await this.loadStations();
            return;
        }

        try {
            const data = await API.getStations(query);
            const stations = data.results || data || [];
            this.displayStations(stations);

            // Fit map to results
            if (stations.length > 0) {
                const lats = stations.map(s => s.latitude);
                const lngs = stations.map(s => s.longitude);
                this.map.fitBounds([
                    [Math.min(...lats), Math.min(...lngs)],
                    [Math.max(...lats), Math.max(...lngs)]
                ]);
            } else {
                // If no station matches locally, search via Nominatim
                this.searchNominatim(query);
            }
        } catch (error) {
            console.error('Search error:', error);
        }
    },

    // ─── Nominatim Search ───────────────────────────────
    async searchNominatim(query) {
        try {
            // Include Nashik context since we are focused there
            let searchQuery = query;
            if (!query.toLowerCase().includes('nashik')) {
                searchQuery += ' Nashik, Maharashtra';
            }
            const res = await fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(searchQuery)}`);
            const data = await res.json();
            if (data && data.length > 0) {
                const { lat, lon } = data[0];
                this.map.panTo([lat, lon]);
                this.map.setZoom(15);
            } else {
                Utils.showToast('No locations found', 'error');
            }
        } catch (e) {
            console.error(e);
        }
    }
};
