# Smart CNG Station Finder

Smart CNG Station Finder is a Django-based web application that helps CNG vehicle users find nearby stations, compare current crowd and availability reports, view routes, save favorite stations, and reserve refueling time slots.

It addresses a practical problem for CNG drivers: station information, queue length, and gas availability can change quickly. The application brings station discovery, community queue updates, and booking management into one place.

## Features

- Search active stations by name or address.
- Use browser geolocation to find stations within a configurable radius.
- Display stations on an interactive Leaflet map with status-colored markers.
- Sort nearby stations by distance, queue length, or a smart score based on distance, queue, and reported availability.
- Show a best-station recommendation for the current location.
- Display queue length, gas availability, recent crowd reports, and report reliability votes.
- Submit, upvote, downvote, and review recent queue updates. Reports older than 60 minutes are excluded from current queue results.
- Register and log in with a custom user profile containing vehicle information.
- View station details, contact information, pricing when available, coordinates, and available time slots.
- Book a future slot, receive a short booking token, view booking history, and cancel eligible bookings.
- Save and remove favorite stations.
- Provide staff users with a separate control panel for station, booking, and user management.
- Toggle a queue-intensity heatmap on the station map.

## Technologies Used

| Area | Technologies |
| --- | --- |
| Backend | Python, Django 5, Django REST Framework |
| Authentication | Django sessions, Simple JWT access and refresh tokens |
| Database | SQLite with Django ORM and migrations |
| Frontend | Django templates, HTML, CSS, JavaScript |
| Map and routing | Leaflet, OpenStreetMap tiles, OSRM routing |
| External data services | OpenStreetMap Overpass API, Nominatim, Google Directions API|


## How It Works

1. Django serves the HTML templates and static frontend assets. The browser-side `API` module communicates with REST endpoints under `/api/`.
2. On the home page, the application requests browser geolocation. If permission is granted, the map centers on the user and requests active stations within a 50 km radius. Without permission, it uses Nashik as the default map center and loads active stations without location filtering.
3. The backend calculates distances with the Haversine formula and returns station status, recent queue data, and distance information. Search uses station name and address fields.
4. Leaflet renders the station markers and sidebar. The user can sort results, open station details, request a route, or inspect the queue and booking controls.
5. A smart recommendation scores stations using distance, average recent queue length, and an availability penalty. The heatmap endpoint converts queue intensity into weighted map points.
6. Authenticated users receive JWT access and refresh tokens, which the frontend stores in `localStorage`. Failed requests with an expired access token attempt a refresh before retrying.
7. Booking requests validate the station-slot relationship, selected date, slot capacity, duplicate bookings, and user role before creating a confirmed booking.
8. Staff users access the Django-backed control panel to manage stations, booking status, and user status/history.

## Application Flow

```text
Browser
  |
  +--> Django templates and static JavaScript
          |
          +--> Request geolocation or use Nashik fallback
          |
          +--> Django REST API --> SQLite station, queue, user, and booking data
          |          |
          |          +--> Search, nearby sorting, smart recommendation, heatmap
          |          +--> JWT authentication and profile management
          |          +--> Slot booking, cancellation, favorites, queue votes
          |
          +--> Leaflet map --> OpenStreetMap tiles and OSRM route display
          +--> Optional backend proxies --> Google Directions and Places APIs
```

## Project Structure

```text
SmartCNG_Web/
├── manage.py
├── requirements.txt
├── .env.example
├── db.sqlite3                         # Local database when present
├── smartcng/
│   ├── settings.py                    # Django, database, JWT, CORS, and static-file settings
│   ├── urls.py                        # API and template routing
│   ├── config_urls.py                 # Maps configuration endpoint
│   └── wsgi.py
├── accounts/                          # Custom user, registration, login, profile API
├── stations/                          # Stations, queue updates, favorites, map proxies
│   └── management/commands/
│       ├── fetch_stations.py          # Import CNG stations through Overpass
│       └── seed_slots.py              # Create default station time slots
├── bookings/                          # Slots, bookings, serializers, and API views
├── control_panel/                     # Staff-only management views and forms
└── frontend/
    ├── templates/                     # Public, account, booking, station, and admin pages
    └── static/
        ├── css/                       # Main and light-theme stylesheets
        └── js/                        # API, map, booking, queue, and UI utilities
```

## Installation and Setup

### 1. Create and activate a virtual environment

PowerShell:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

On macOS or Linux:

```bash
python -m venv venv
source venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Create a local `.env` file from the provided example and replace placeholder values locally:

```powershell
Copy-Item .env.example .env
```

The supported variables are `DJANGO_SECRET_KEY`, `DEBUG`, and `GOOGLE_MAPS_API_KEY`. Never commit `.env` or real keys.

### 4. Initialize the database and seed data

```bash
python manage.py migrate
python manage.py fetch_stations
python manage.py seed_slots
```

`fetch_stations` queries the OpenStreetMap Overpass API around Nashik by default. If that request fails, the command loads its built-in seed station records. Use `--lat`, `--lng`, and `--radius` to change the import center and radius in meters.

Create a staff account when needed:

```bash
python manage.py createsuperuser
```

### 5. Run the development server

```bash
python manage.py runserver
```

Open `http://127.0.0.1:8000/`. Staff users can use `/admin-dashboard/` for the application control panel or `/admin/` for Django admin.

## API and External Services

The frontend uses the Django REST API at `/api/`. The main API groups cover authentication and profiles, station search and nearby results, queue updates and votes, favorites, slot availability, and booking management. DRF is configured for JWT and session authentication, filtering/search backends, and page-number pagination.

External services used by the implementation are:

- **OpenStreetMap:** Leaflet map tiles and the Nominatim fallback used when a local station search has no match.
- **OSRM via OpenStreetMap directions:** Route lines and the external directions link shown by the map UI.
- **Overpass API:** The `fetch_stations` management command imports CNG-tagged fuel stations into SQLite.


## Screenshots

No screenshot files are currently included in the repository. Add captured images to a tracked `screenshots/` directory and reference them here, for example:

```markdown
![Home map view](screenshots/home.png)
```

## Key Learning Outcomes

- Designing a Django project with multiple apps, a custom user model, ORM relationships, migrations, and admin configuration.
- Building REST endpoints with Django REST Framework serializers, permissions, filtering, pagination, and validation.
- Implementing JWT access/refresh handling alongside Django session authentication.
- Integrating browser geolocation, asynchronous JavaScript `fetch`, debounced search, and local storage.
- Applying the Haversine formula and a weighted ranking function to location-aware recommendations.
- Rendering interactive maps, routes, markers, and heatmap data with Leaflet.
- Modeling booking capacity, duplicate-booking rules, queue expiry, favorites, and vote tracking.

## Challenges and Technical Highlights

1. Combining location-aware station discovery with a fallback experience when geolocation is denied or unavailable.
2. Keeping queue information useful by expiring reports after 60 minutes and calculating a reliability score from community votes.
3. Implementing booking validation across users, stations, slots, dates, capacity, duplicate bookings, and staff restrictions.
4. Providing a smart station recommendation that balances proximity, current crowd estimates, and reported gas availability.
5. Separating public station reads from authenticated user actions and staff-only management views.

## Future Improvements

- Add automated backend and frontend tests for authentication, capacity handling, permissions, and map/search flows.
- Add database-level transaction/locking safeguards for simultaneous bookings.
- Add production deployment settings, restricted CORS/hosts, secure secret handling, and API rate limiting.
- Add server-side caching or scheduled synchronization for external station data.
- Improve route-provider configuration and add clearer handling when external map services are unavailable.
- Add richer station operating-hours, pricing, and availability validation where reliable data is available.

## Limitations

- Station and queue data accuracy depends on the Overpass import and user-submitted reports; queue reports are not a guaranteed live feed.
- The default database is SQLite, which is suitable for local development but not ideal for a high-concurrency production deployment.
- Map tiles, geocoding, routing, and Google proxy features depend on third-party service availability and configuration.
- The current settings enable debug mode by default, allow all hosts, and allow all CORS origins; these settings require hardening before production use.
- The repository does not currently include a test suite or screenshot assets.

## Author

**Shrushti Sanap**  
GitHub: [shrushti87](https://github.com/shrushti87)

## License

This project is an educational project created for learning and demonstration purposes. No separate license file is currently included.