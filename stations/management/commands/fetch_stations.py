"""
Management command to fetch CNG stations from Google Places API.
Usage: python manage.py fetch_stations --lat 19.076 --lng 72.8777 --radius 50000
"""
import requests
from django.core.management.base import BaseCommand
from django.conf import settings
from stations.models import Station


class Command(BaseCommand):
    help = 'Fetch CNG stations from Google Places API and store in database'

    def add_arguments(self, parser):
        parser.add_argument('--lat', type=float, default=20.0110,
                            help='Latitude for search center (default: Nashik)')
        parser.add_argument('--lng', type=float, default=73.7903,
                            help='Longitude for search center (default: Nashik)')
        parser.add_argument('--radius', type=int, default=50000,
                            help='Search radius in meters (default: 50000)')

    def handle(self, *args, **options):
        lat = options['lat']
        lng = options['lng']
        radius = options['radius']

        self.stdout.write(f'Fetching CNG stations near ({lat}, {lng}) with radius {radius}m using Overpass API...')

        overpass_url = "https://overpass-api.de/api/interpreter"
        overpass_query = f"""
        [out:json];
        (
          node["amenity"="fuel"]["fuel:cng"="yes"](around:{radius},{lat},{lng});
          way["amenity"="fuel"]["fuel:cng"="yes"](around:{radius},{lat},{lng});
          relation["amenity"="fuel"]["fuel:cng"="yes"](around:{radius},{lat},{lng});
        );
        out center;
        """

        created_count = 0
        updated_count = 0

        try:
            headers = {'User-Agent': 'SmartCNG/1.0 (test@example.com)'}
            response = requests.post(overpass_url, data={'data': overpass_query}, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Overpass API request failed: {e}'))
            self.stdout.write(self.style.WARNING('Loading seed data instead.'))
            self._load_seed_data()
            return

        elements = data.get('elements', [])
        for element in elements:
            place_id = str(element.get('id'))
            if not place_id:
                continue

            tags = element.get('tags', {})
            
            lat_val = element.get('lat') or element.get('center', {}).get('lat', 0)
            lng_val = element.get('lon') or element.get('center', {}).get('lon', 0)

            name = tags.get('name', 'Unknown CNG Station')
            address = tags.get('addr:full', '')
            if not address:
                street = tags.get('addr:street', '')
                city = tags.get('addr:city', '')
                address = f"{street}, {city}".strip(', ')

            station_data = {
                'name': name,
                'address': address if address else 'Nashik, Maharashtra',
                'latitude': lat_val,
                'longitude': lng_val,
                'rating': 4.0,
            }

            station, created = Station.objects.update_or_create(
                place_id=place_id,
                defaults=station_data
            )

            if created:
                created_count += 1
            else:
                updated_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'Done! Created: {created_count}, Updated: {updated_count}'
        ))

    def _load_seed_data(self):
        """Load seed/dummy station data when API key is not available."""
        seed_stations = [
            {
                'name': 'Mahanagar Gas CNG Station - Andheri',
                'address': 'Andheri East, Mumbai, Maharashtra 400069',
                'latitude': 19.1136,
                'longitude': 72.8697,
                'place_id': 'seed_andheri_001',
                'price_per_kg': 89.96,
                'rating': 4.2,
                'status': 'available',
            },
            {
                'name': 'Adani CNG Station - Bandra',
                'address': 'Bandra West, Mumbai, Maharashtra 400050',
                'latitude': 19.0596,
                'longitude': 72.8295,
                'place_id': 'seed_bandra_002',
                'price_per_kg': 89.96,
                'rating': 3.8,
                'status': 'available',
            },
            {
                'name': 'MGL CNG Station - Dadar',
                'address': 'Dadar TT, Mumbai, Maharashtra 400014',
                'latitude': 19.0178,
                'longitude': 72.8478,
                'place_id': 'seed_dadar_003',
                'price_per_kg': 89.96,
                'rating': 4.0,
                'status': 'low',
            },
            {
                'name': 'AG CNG Station - Powai',
                'address': 'Hiranandani Gardens, Powai, Mumbai 400076',
                'latitude': 19.1196,
                'longitude': 72.9051,
                'place_id': 'seed_powai_004',
                'price_per_kg': 89.96,
                'rating': 4.5,
                'status': 'available',
            },
            {
                'name': 'Bharat Petroleum CNG - Malad',
                'address': 'Malad West, Mumbai, Maharashtra 400064',
                'latitude': 19.1872,
                'longitude': 72.8484,
                'place_id': 'seed_malad_005',
                'price_per_kg': 89.96,
                'rating': 3.5,
                'status': 'available',
            },
            {
                'name': 'Indian Oil CNG Station - Thane',
                'address': 'Thane West, Maharashtra 400601',
                'latitude': 19.2183,
                'longitude': 72.9781,
                'place_id': 'seed_thane_006',
                'price_per_kg': 89.96,
                'rating': 4.1,
                'status': 'available',
            },
            {
                'name': 'GAIL CNG Pump - Borivali',
                'address': 'Borivali East, Mumbai, Maharashtra 400066',
                'latitude': 19.2307,
                'longitude': 72.8567,
                'place_id': 'seed_borivali_007',
                'price_per_kg': 89.96,
                'rating': 3.9,
                'status': 'low',
            },
            {
                'name': 'MGL Gas Station - Kurla',
                'address': 'Kurla West, Mumbai, Maharashtra 400070',
                'latitude': 19.0726,
                'longitude': 72.8794,
                'place_id': 'seed_kurla_008',
                'price_per_kg': 89.96,
                'rating': 3.7,
                'status': 'available',
            },
            {
                'name': 'Torrent Gas CNG - Goregaon',
                'address': 'Goregaon East, Mumbai, Maharashtra 400063',
                'latitude': 19.1663,
                'longitude': 72.8526,
                'place_id': 'seed_goregaon_009',
                'price_per_kg': 89.96,
                'rating': 4.3,
                'status': 'available',
            },
            {
                'name': 'HP CNG Station - Vashi',
                'address': 'Vashi, Navi Mumbai, Maharashtra 400703',
                'latitude': 19.0771,
                'longitude': 72.9988,
                'place_id': 'seed_vashi_010',
                'price_per_kg': 89.96,
                'rating': 4.0,
                'status': 'no_gas',
            },
            {
                'name': 'MGL CNG Station - Chembur',
                'address': 'Chembur East, Mumbai, Maharashtra 400071',
                'latitude': 19.0522,
                'longitude': 72.8994,
                'place_id': 'seed_chembur_011',
                'price_per_kg': 89.96,
                'rating': 3.6,
                'status': 'available',
            },
            {
                'name': 'Adani Gas CNG - Kandivali',
                'address': 'Kandivali West, Mumbai, Maharashtra 400067',
                'latitude': 19.2046,
                'longitude': 72.8370,
                'place_id': 'seed_kandivali_012',
                'price_per_kg': 89.96,
                'rating': 4.1,
                'status': 'available',
            },
            {
                'name': 'IOCL CNG Station - Navi Mumbai',
                'address': 'Airoli, Navi Mumbai, Maharashtra 400708',
                'latitude': 19.1547,
                'longitude': 72.9974,
                'place_id': 'seed_airoli_013',
                'price_per_kg': 89.96,
                'rating': 4.4,
                'status': 'available',
            },
            {
                'name': 'MGL CNG Pump - Mulund',
                'address': 'Mulund West, Mumbai, Maharashtra 400080',
                'latitude': 19.1726,
                'longitude': 72.9425,
                'place_id': 'seed_mulund_014',
                'price_per_kg': 89.96,
                'rating': 3.8,
                'status': 'available',
            },
            {
                'name': 'AG CNG Station - Vikhroli',
                'address': 'Vikhroli East, Mumbai, Maharashtra 400079',
                'latitude': 19.1092,
                'longitude': 72.9279,
                'place_id': 'seed_vikhroli_015',
                'price_per_kg': 89.96,
                'rating': 4.0,
                'status': 'low',
            },
            {
                'name': 'Delhi CNG Station - Connaught Place',
                'address': 'Connaught Place, New Delhi, Delhi 110001',
                'latitude': 28.6315,
                'longitude': 77.2167,
                'place_id': 'seed_delhi_cp_016',
                'price_per_kg': 76.59,
                'rating': 4.1,
                'status': 'available',
            },
            {
                'name': 'IGL CNG Station - Noida Sector 18',
                'address': 'Sector 18, Noida, UP 201301',
                'latitude': 28.5707,
                'longitude': 77.3219,
                'place_id': 'seed_noida_017',
                'price_per_kg': 76.59,
                'rating': 3.9,
                'status': 'available',
            },
            {
                'name': 'Adani CNG Station - Ahmedabad',
                'address': 'SG Highway, Ahmedabad, Gujarat 380054',
                'latitude': 23.0225,
                'longitude': 72.5714,
                'place_id': 'seed_ahmedabad_018',
                'price_per_kg': 72.41,
                'rating': 4.3,
                'status': 'available',
            },
            {
                'name': 'Gujarat Gas CNG - Surat',
                'address': 'Ring Road, Surat, Gujarat 395002',
                'latitude': 21.1702,
                'longitude': 72.8311,
                'place_id': 'seed_surat_019',
                'price_per_kg': 72.41,
                'rating': 4.0,
                'status': 'available',
            },
            {
                'name': 'MGL CNG Station - Pune',
                'address': 'Hinjewadi, Pune, Maharashtra 411057',
                'latitude': 18.5912,
                'longitude': 73.7389,
                'place_id': 'seed_pune_020',
                'price_per_kg': 89.96,
                'rating': 4.2,
                'status': 'available',
            },
        ]

        created_count = 0
        for station_data in seed_stations:
            _, created = Station.objects.update_or_create(
                place_id=station_data['place_id'],
                defaults=station_data
            )
            if created:
                created_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'Loaded {created_count} seed stations'
        ))
