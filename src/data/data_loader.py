import pandas as pd
import requests
import logging
import sqlite3
from typing import Optional, Dict, List, Tuple
from geopy.distance import geodesic
from src.config import Config

class DataLoader:
    def __init__(self):
        self.parking_signs_df = None
        self.meter_zones_df = None
        self.db_path = Config.SQLITE_DB_PATH
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database for parking violations."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create violations table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS violations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    summons_number TEXT UNIQUE,
                    plate_id TEXT,
                    registration_state TEXT,
                    plate_type TEXT,
                    issue_date TEXT,
                    violation_code INTEGER,
                    vehicle_body_type TEXT,
                    vehicle_make TEXT,
                    issuing_agency TEXT,
                    street_code1 INTEGER,
                    street_code2 INTEGER,
                    street_code3 INTEGER,
                    vehicle_expiration_date TEXT,
                    violation_location TEXT,
                    violation_precinct INTEGER,
                    issuer_precinct INTEGER,
                    issuer_code INTEGER,
                    issuer_command TEXT,
                    issuer_squad TEXT,
                    violation_time TEXT,
                    time_first_observed TEXT,
                    violation_county TEXT,
                    violation_in_front_of_or_opposite TEXT,
                    house_number TEXT,
                    street_name TEXT,
                    intersecting_street TEXT,
                    date_first_observed TEXT,
                    law_section INTEGER,
                    sub_division TEXT,
                    violation_legal_code TEXT,
                    days_parking_in_effect TEXT,
                    from_hours_in_effect TEXT,
                    to_hours_in_effect TEXT,
                    vehicle_color TEXT,
                    unregistered_vehicle TEXT,
                    vehicle_year INTEGER,
                    meter_number TEXT,
                    feet_from_curb INTEGER,
                    violation_post_code TEXT,
                    violation_description TEXT,
                    no_standing_or_stopping_violation TEXT,
                    hydrant_violation TEXT,
                    double_parking_violation TEXT,
                    latitude REAL,
                    longitude REAL,
                    community_board INTEGER,
                    community_council INTEGER,
                    census_tract INTEGER,
                    bin INTEGER,
                    bbl TEXT,
                    nta TEXT,
                    borough TEXT,
                    fine_amount REAL
                )
            ''')
            
            conn.commit()
            conn.close()
            logging.info("Database initialized successfully")
            
        except Exception as e:
            logging.error(f"Error initializing database: {e}")
    
    def load_parking_signs(self) -> bool:
        """Load parking signs data from NYC Open Data."""
        try:
            logging.info("Fetching parking signs data from NYC Open Data...")
            
            # Build request URL with limit
            url = f"{Config.PARKING_SIGNS_URL}?$limit={Config.MAX_RECORDS_PER_REQUEST}"
            logging.info(f"Requesting URL: {url}")
            
            # Add headers to mimic a browser request
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'application/json',
                'Accept-Language': 'en-US,en;q=0.9',
            }
            
            response = requests.get(url, timeout=30, headers=headers)
            logging.info(f"Response status: {response.status_code}")
            
            if response.status_code == 403:
                logging.warning("Received 403 Forbidden. Trying with smaller limit...")
                # Try with a smaller limit
                url_small = f"{Config.PARKING_SIGNS_URL}?$limit=1000"
                response = requests.get(url_small, timeout=30, headers=headers)
                logging.info(f"Small limit response status: {response.status_code}")
            
            response.raise_for_status()
            
            data = response.json()
            logging.info(f"Received {len(data)} parking sign records")
            self.parking_signs_df = pd.DataFrame(data)
            
            # Clean and process the data
            if not self.parking_signs_df.empty:
                # Check if we have State Plane coordinates (sign_x_coord, sign_y_coord)
                if 'sign_x_coord' in self.parking_signs_df.columns and 'sign_y_coord' in self.parking_signs_df.columns:
                    # Convert State Plane coordinates to lat/lon
                    self.parking_signs_df['sign_x_coord'] = pd.to_numeric(
                        self.parking_signs_df['sign_x_coord'], errors='coerce'
                    )
                    self.parking_signs_df['sign_y_coord'] = pd.to_numeric(
                        self.parking_signs_df['sign_y_coord'], errors='coerce'
                    )
                    
                    # Convert NY State Plane coordinates to lat/lon
                    self.parking_signs_df = self._convert_state_plane_to_latlon(self.parking_signs_df)
                
                # Try to get lat/lon columns (fallback)
                elif 'latitude' in self.parking_signs_df.columns and 'longitude' in self.parking_signs_df.columns:
                    self.parking_signs_df['latitude'] = pd.to_numeric(
                        self.parking_signs_df.get('latitude', 0), errors='coerce'
                    )
                    self.parking_signs_df['longitude'] = pd.to_numeric(
                        self.parking_signs_df.get('longitude', 0), errors='coerce'
                    )
                else:
                    logging.warning("No coordinate columns found in parking signs data")
                    self._create_sample_parking_signs()
                    return True
                
                # Remove rows with invalid coordinates
                if 'latitude' in self.parking_signs_df.columns and 'longitude' in self.parking_signs_df.columns:
                    self.parking_signs_df = self.parking_signs_df.dropna(
                        subset=['latitude', 'longitude']
                    )
                    
                    # Filter out obviously wrong coordinates (outside NYC area)
                    nyc_bounds = {
                        'lat_min': 40.4774, 'lat_max': 40.9176,
                        'lon_min': -74.2591, 'lon_max': -73.7004
                    }
                    
                    self.parking_signs_df = self.parking_signs_df[
                        (self.parking_signs_df['latitude'] >= nyc_bounds['lat_min']) &
                        (self.parking_signs_df['latitude'] <= nyc_bounds['lat_max']) &
                        (self.parking_signs_df['longitude'] >= nyc_bounds['lon_min']) &
                        (self.parking_signs_df['longitude'] <= nyc_bounds['lon_max'])
                    ]
                
                logging.info(f"Loaded {len(self.parking_signs_df)} parking sign records")
                return True
            else:
                logging.warning("No parking signs data received, creating sample data...")
                self._create_sample_parking_signs()
                return True
                
        except Exception as e:
            logging.error(f"Error loading parking signs data: {e}")
            import traceback
            logging.error(f"Full traceback: {traceback.format_exc()}")
            
            # Create sample parking signs data as fallback
            logging.info("Creating sample parking signs data as fallback...")
            self._create_sample_parking_signs()
            return True
    
    def load_meter_zones(self) -> bool:
        """Load parking meter zones data from NYC Open Data."""
        try:
            logging.info("Fetching meter zones data from NYC Open Data...")
            
            url = f"{Config.METER_ZONES_URL}?$limit={Config.MAX_RECORDS_PER_REQUEST}"
            
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            self.meter_zones_df = pd.DataFrame(data)
            
            if not self.meter_zones_df.empty:
                # Process coordinates from the new dataset
                # Convert lat/long to numeric (this dataset uses 'lat' and 'long')
                if 'lat' in self.meter_zones_df.columns:
                    self.meter_zones_df['lat'] = pd.to_numeric(
                        self.meter_zones_df['lat'], errors='coerce'
                    )
                if 'long' in self.meter_zones_df.columns:
                    self.meter_zones_df['long'] = pd.to_numeric(
                        self.meter_zones_df['long'], errors='coerce'
                    )
                
                # Remove rows with invalid coordinates
                if 'lat' in self.meter_zones_df.columns and 'long' in self.meter_zones_df.columns:
                    self.meter_zones_df = self.meter_zones_df.dropna(
                        subset=['lat', 'long']
                    )
                    
                    # Filter NYC bounds
                    nyc_bounds = {
                        'lat_min': 40.4774, 'lat_max': 40.9176,
                        'lon_min': -74.2591, 'lon_max': -73.7004
                    }
                    
                    self.meter_zones_df = self.meter_zones_df[
                        (self.meter_zones_df['lat'] >= nyc_bounds['lat_min']) &
                        (self.meter_zones_df['lat'] <= nyc_bounds['lat_max']) &
                        (self.meter_zones_df['long'] >= nyc_bounds['lon_min']) &
                        (self.meter_zones_df['long'] <= nyc_bounds['lon_max'])
                    ]
                
                logging.info(f"Loaded {len(self.meter_zones_df)} meter zone records")
                return True
            else:
                logging.warning("No meter zones data received")
                return False
                
        except Exception as e:
            logging.error(f"Error loading meter zones data: {e}")
            return False
    
    def find_nearby_parking_signs(
        self, 
        lat: float, 
        lon: float, 
        radius_meters: int = None
    ) -> List[Dict]:
        """Find parking signs within radius of given coordinates."""
        if self.parking_signs_df is None or self.parking_signs_df.empty:
            return []
        
        if radius_meters is None:
            radius_meters = Config.SEARCH_RADIUS_METERS
        
        try:
            # Filter by approximate bounds first (faster)
            # Roughly 0.001 degrees = ~111 meters
            buffer_deg = (radius_meters / 111000) * 1.5  # Add some buffer
            
            nearby_df = self.parking_signs_df[
                (abs(self.parking_signs_df['latitude'] - lat) <= buffer_deg) &
                (abs(self.parking_signs_df['longitude'] - lon) <= buffer_deg)
            ]
            
            if nearby_df.empty:
                return []
            
            # Calculate exact distances
            target_point = (lat, lon)
            nearby_signs = []
            
            for _, row in nearby_df.iterrows():
                sign_point = (row['latitude'], row['longitude'])
                distance = geodesic(target_point, sign_point).meters
                
                if distance <= radius_meters:
                    sign_data = row.to_dict()
                    sign_data['distance_meters'] = round(distance, 1)
                    nearby_signs.append(sign_data)
            
            # Sort by distance
            nearby_signs.sort(key=lambda x: x['distance_meters'])
            
            return nearby_signs
            
        except Exception as e:
            logging.error(f"Error finding nearby parking signs: {e}")
            return []
    
    def find_nearest_meter_zone(self, lat: float, lon: float) -> Optional[Dict]:
        """Find the nearest parking meter zone."""
        if self.meter_zones_df is None or self.meter_zones_df.empty:
            return None
        
        # Check if we have lat/long columns (different naming in this dataset)
        if 'lat' not in self.meter_zones_df.columns or 'long' not in self.meter_zones_df.columns:
            return None
        
        try:
            # Filter by approximate bounds first (faster)
            radius_meters = 500  # Search within 500m for meters
            buffer_deg = (radius_meters / 111000) * 1.5
            
            # Convert string coordinates to float first
            meter_lats = pd.to_numeric(self.meter_zones_df['lat'], errors='coerce')
            meter_longs = pd.to_numeric(self.meter_zones_df['long'], errors='coerce')
            
            nearby_df = self.meter_zones_df[
                (abs(meter_lats - lat) <= buffer_deg) &
                (abs(meter_longs - lon) <= buffer_deg)
            ]
            
            if nearby_df.empty:
                return None
            
            # Calculate exact distances and find the nearest
            target_point = (lat, lon)
            min_distance = float('inf')
            nearest_meter = None
            
            for _, row in nearby_df.head(20).iterrows():  # Limit to first 20 for performance
                try:
                    meter_lat = float(row['lat'])
                    meter_lon = float(row['long'])
                    meter_point = (meter_lat, meter_lon)
                    distance = geodesic(target_point, meter_point).meters
                except (ValueError, TypeError):
                    continue  # Skip invalid coordinates
                
                if distance < min_distance:
                    min_distance = distance
                    nearest_meter = row.to_dict()
                    nearest_meter['distance_meters'] = round(distance, 1)
            
            return nearest_meter
            
        except Exception as e:
            logging.error(f"Error finding nearest meter zone: {e}")
            return None
    
    def get_violation_trends(
        self, 
        borough: str = None, 
        year: int = None
    ) -> Dict:
        """Get violation trends from the database."""
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Build query
            query = """
                SELECT 
                    violation_description,
                    COUNT(*) as violation_count,
                    AVG(fine_amount) as avg_fine
                FROM violations 
                WHERE 1=1
            """
            params = []
            
            if borough:
                query += " AND UPPER(borough) = UPPER(?)"
                params.append(borough)
            
            if year:
                query += " AND strftime('%Y', issue_date) = ?"
                params.append(str(year))
            
            query += """
                GROUP BY violation_description 
                ORDER BY violation_count DESC 
                LIMIT 10
            """
            
            df = pd.read_sql_query(query, conn, params=params)
            conn.close()
            
            if df.empty:
                return {
                    'trends': [],
                    'total_violations': 0,
                    'filters': {'borough': borough, 'year': year}
                }
            
            trends = []
            for _, row in df.iterrows():
                trends.append({
                    'violation_type': row['violation_description'],
                    'count': int(row['violation_count']),
                    'avg_fine': round(float(row['avg_fine']) if row['avg_fine'] else 0, 2)
                })
            
            return {
                'trends': trends,
                'total_violations': sum(t['count'] for t in trends),
                'filters': {'borough': borough, 'year': year}
            }
            
        except Exception as e:
            logging.error(f"Error getting violation trends: {e}")
            return {
                'trends': [],
                'total_violations': 0,
                'filters': {'borough': borough, 'year': year},
                'error': str(e)
            }
    
    def load_real_violations(self, limit: int = None) -> bool:
        """Load real violation data from NYC Open Data with geocoding."""
        try:
            if limit is None:
                limit = Config.MAX_VIOLATIONS_TO_LOAD
            
            logging.info(f"Fetching real violations data from NYC Open Data (limit: {limit})...")
            
            # Fetch violations data
            url = f"{Config.VIOLATIONS_URL}?$limit={limit}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json',
            }
            
            response = requests.get(url, timeout=60, headers=headers)
            response.raise_for_status()
            
            violations_data = response.json()
            logging.info(f"Received {len(violations_data)} violation records")
            
            if not violations_data:
                logging.warning("No violations data received")
                return False
            
            # Process violations in batches for geocoding
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get violation code descriptions
            violation_codes = self._get_violation_code_descriptions()
            
            processed_count = 0
            geocoded_count = 0
            
            # Process in batches to manage memory and API rate limits
            batch_size = Config.GEOCODING_BATCH_SIZE
            
            for i in range(0, len(violations_data), batch_size):
                batch = violations_data[i:i + batch_size]
                logging.info(f"Processing batch {i//batch_size + 1}/{(len(violations_data)-1)//batch_size + 1}")
                
                for violation in batch:
                    try:
                        # Build address from violation data
                        address_parts = []
                        
                        if violation.get('violation_location'):
                            address_parts.append(violation['violation_location'])
                        
                        if violation.get('street_name'):
                            address_parts.append(violation['street_name'])
                        
                        if violation.get('intersecting_street'):
                            address_parts.append(f"near {violation['intersecting_street']}")
                        
                        # Add NYC to help geocoding
                        address_parts.append("New York, NY")
                        
                        address = " ".join(address_parts)
                        
                        # Geocode the address
                        lat, lon = self._geocode_address(address)
                        
                        if lat and lon:
                            geocoded_count += 1
                        
                        # Get violation description
                        violation_code = violation.get('violation_code', '')
                        violation_description = violation_codes.get(violation_code, f"Violation Code {violation_code}")
                        
                        # Calculate fine amount (simplified mapping)
                        fine_amount = self._get_fine_amount(violation_code)
                        
                        # Get borough from county code
                        borough = self._get_borough_from_county(violation.get('violation_county', ''))
                        
                        # Insert into database
                        cursor.execute('''
                            INSERT OR REPLACE INTO violations 
                            (summons_number, plate_id, registration_state, plate_type, 
                             issue_date, violation_code, vehicle_body_type, vehicle_make,
                             issuing_agency, street_name, intersecting_street, 
                             violation_location, violation_description, violation_county,
                             borough, fine_amount, latitude, longitude)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            violation.get('summons_number'),
                            violation.get('plate_id'),
                            violation.get('registration_state'),
                            violation.get('plate_type'),
                            violation.get('issue_date'),
                            violation.get('violation_code'),
                            violation.get('vehicle_body_type'),
                            violation.get('vehicle_make'),
                            violation.get('issuing_agency'),
                            violation.get('street_name'),
                            violation.get('intersecting_street'),
                            violation.get('violation_location'),
                            violation_description,
                            violation.get('violation_county'),
                            borough,
                            fine_amount,
                            lat,
                            lon
                        ))
                        
                        processed_count += 1
                        
                    except Exception as e:
                        logging.warning(f"Error processing violation {violation.get('summons_number', 'unknown')}: {e}")
                        continue
                
                # Commit batch
                conn.commit()
                
                # Add small delay to be respectful to geocoding API
                import time
                time.sleep(0.1)
            
            conn.close()
            
            logging.info(f"Successfully loaded {processed_count} real violations")
            logging.info(f"Geocoded {geocoded_count} addresses ({geocoded_count/processed_count*100:.1f}%)")
            
            return True
            
        except Exception as e:
            logging.error(f"Error loading real violations: {e}")
            import traceback
            logging.error(f"Full traceback: {traceback.format_exc()}")
            return False
    
    def _geocode_address(self, address: str) -> Tuple[Optional[float], Optional[float]]:
        """Geocode an address using NYC Planning Labs Geosearch API."""
        try:
            params = {
                'text': address,
                'size': 1
            }
            
            response = requests.get(Config.GEOCODING_API_URL, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('features') and len(data['features']) > 0:
                    coordinates = data['features'][0]['geometry']['coordinates']
                    # API returns [longitude, latitude]
                    return coordinates[1], coordinates[0]  # Return lat, lon
            
            return None, None
            
        except Exception as e:
            logging.debug(f"Geocoding failed for address '{address}': {e}")
            return None, None
    
    def _get_violation_code_descriptions(self) -> Dict[str, str]:
        """Get violation code to description mapping."""
        # Common NYC parking violation codes
        return {
            '14': 'NO STANDING-DAY/TIME LIMITS',
            '16': 'NO STANDING-BUS STOP',
            '17': 'NO PARKING-DAY/TIME LIMITS',
            '19': 'NO PARKING-BUS STOP',
            '20': 'NO PARKING-DAY/TIME LIMITS',
            '21': 'NO PARKING-STREET CLEANING',
            '34': 'EXPIRED MUNI METER',
            '35': 'FAIL TO DSPLY MUNI METER RECPT',
            '37': 'EXPIRED METER',
            '38': 'OVERTIME STANDING',
            '40': 'FIRE HYDRANT',
            '46': 'DOUBLE PARKING',
            '47': 'DOUBLE PARKING',
            '50': 'PHTO SCHOOL ZN SPEED VIOLATION',
            '67': 'BLOCKING PEDESTRIAN RAMP',
            '69': 'FAILURE TO STOP AT RED LIGHT',
            '71': 'NO PARKING WHERE PROHIBITED',
            '78': 'NO PARKING-NIGHTTIME',
        }
    
    def _get_fine_amount(self, violation_code: str) -> float:
        """Get fine amount for violation code."""
        # Simplified fine mapping
        fine_mapping = {
            '14': 115, '16': 115, '17': 65, '19': 115, '20': 65,
            '21': 65, '34': 35, '35': 35, '37': 25, '38': 35,
            '40': 115, '46': 115, '47': 115, '50': 50, '67': 165,
            '69': 50, '71': 65, '78': 35
        }
        return fine_mapping.get(violation_code, 50)  # Default $50
    
    def _get_borough_from_county(self, county_code: str) -> str:
        """Convert county code to borough name."""
        county_mapping = {
            'NY': 'MANHATTAN',
            'BX': 'BRONX', 
            'BK': 'BROOKLYN',
            'QN': 'QUEENS',
            'ST': 'STATEN ISLAND'
        }
        return county_mapping.get(county_code, 'UNKNOWN')

    def load_sample_violations(self, sample_size: int = 1000):
        """Load sample violation data for demonstration."""
        try:
            # This would normally load from the Kaggle dataset
            # For now, create sample data
            import random
            from datetime import datetime, timedelta
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Sample violation types and fines
            violation_types = [
                ('NO PARKING-STREET CLEANING', 65),
                ('PHTO SCHOOL ZN SPEED VIOLATION', 50),
                ('FAIL TO DSPLY MUNI METER RECPT', 35),
                ('NO STANDING-DAY/TIME LIMITS', 115),
                ('EXPIRED MUNI METER', 35),
                ('NO PARKING-DAY/TIME LIMITS', 65),
                ('EXPIRED METER', 25),
                ('NO STANDING-BUS STOP', 115),
                ('DOUBLE PARKING', 115),
                ('FIRE HYDRANT', 115)
            ]
            
            boroughs = ['MANHATTAN', 'BROOKLYN', 'QUEENS', 'BRONX', 'STATEN ISLAND']
            
            # Generate sample data
            for i in range(sample_size):
                violation_type, fine = random.choice(violation_types)
                borough = random.choice(boroughs)
                
                # Random date in last year
                days_back = random.randint(1, 365)
                issue_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
                
                # Random NYC coordinates
                lat = random.uniform(40.4774, 40.9176)
                lon = random.uniform(-74.2591, -73.7004)
                
                cursor.execute('''
                    INSERT OR IGNORE INTO violations 
                    (summons_number, issue_date, violation_description, 
                     borough, fine_amount, latitude, longitude)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    f'SAMPLE{i:06d}',
                    issue_date,
                    violation_type,
                    borough,
                    fine,
                    lat,
                    lon
                ))
            
            conn.commit()
            conn.close()
            
            logging.info(f"Generated {sample_size} sample violation records")
            
        except Exception as e:
            logging.error(f"Error loading sample violations: {e}")
    
    def _create_sample_parking_signs(self):
        """Create sample parking signs data for demonstration."""
        try:
            import random
            
            # Sample parking sign types
            sign_types = [
                "NO PARKING 8AM-6PM MON-FRI",
                "NO STANDING 7AM-7PM EXCEPT SUNDAY",
                "NO PARKING STREET CLEANING TUESDAY 11AM-2PM",
                "2 HOUR PARKING 9AM-6PM MON-SAT",
                "NO PARKING ANYTIME",
                "METERED PARKING 9AM-6PM MON-SAT",
                "NO STANDING 7AM-7PM",
                "NO PARKING 8AM-6PM EXCEPT SUNDAY",
                "1 HOUR PARKING 9AM-6PM MON-SAT",
                "NO PARKING STREET CLEANING WEDNESDAY 11AM-2PM"
            ]
            
            # NYC coordinate bounds
            nyc_bounds = {
                'lat_min': 40.4774, 'lat_max': 40.9176,
                'lon_min': -74.2591, 'lon_max': -73.7004
            }
            
            # Create sample data
            sample_data = []
            for i in range(1000):  # Create 1000 sample signs
                lat = random.uniform(nyc_bounds['lat_min'], nyc_bounds['lat_max'])
                lon = random.uniform(nyc_bounds['lon_min'], nyc_bounds['lon_max'])
                
                sample_data.append({
                    'latitude': lat,
                    'longitude': lon,
                    'sign_description': random.choice(sign_types),
                    'street_name': f"Sample Street {i % 100}",
                    'cross_street': f"Cross Street {i % 50}",
                    'sign_id': f"SAMPLE{i:06d}",
                    'borough': random.choice(['MANHATTAN', 'BROOKLYN', 'QUEENS', 'BRONX', 'STATEN ISLAND'])
                })
            
            self.parking_signs_df = pd.DataFrame(sample_data)
            logging.info(f"Created {len(self.parking_signs_df)} sample parking sign records")
            
        except Exception as e:
            logging.error(f"Error creating sample parking signs: {e}")
            # Create minimal fallback
            self.parking_signs_df = pd.DataFrame({
                'latitude': [40.7589],
                'longitude': [-73.9851],
                'sign_description': ['NO PARKING 8AM-6PM MON-FRI'],
                'street_name': ['Sample Street'],
                'cross_street': ['Cross Street'],
                'sign_id': ['SAMPLE001'],
                'borough': ['MANHATTAN']
            })
    
    def _convert_state_plane_to_latlon(self, df):
        """Convert NY State Plane coordinates to latitude/longitude."""
        try:
            # Install pyproj if needed for coordinate conversion
            try:
                from pyproj import Transformer
            except ImportError:
                logging.warning("pyproj not available, using approximate conversion")
                return self._approximate_state_plane_conversion(df)
            
            # NY State Plane coordinate system (EPSG:2263 - NAD83 / New York Long Island)
            transformer = Transformer.from_crs("EPSG:2263", "EPSG:4326", always_xy=True)
            
            # Convert coordinates
            valid_coords = df.dropna(subset=['sign_x_coord', 'sign_y_coord'])
            
            if not valid_coords.empty:
                lons, lats = transformer.transform(
                    valid_coords['sign_x_coord'].values,
                    valid_coords['sign_y_coord'].values
                )
                
                # Create new dataframe with converted coordinates
                converted_df = df.copy()
                converted_df.loc[valid_coords.index, 'longitude'] = lons
                converted_df.loc[valid_coords.index, 'latitude'] = lats
                
                logging.info(f"Converted {len(valid_coords)} coordinate pairs from State Plane to lat/lon")
                return converted_df
            else:
                logging.warning("No valid State Plane coordinates found")
                return df
                
        except Exception as e:
            logging.error(f"Error converting coordinates: {e}")
            return self._approximate_state_plane_conversion(df)
    
    def _approximate_state_plane_conversion(self, df):
        """Approximate conversion from NY State Plane to lat/lon using linear approximation."""
        try:
            # Approximate conversion factors for NYC area
            # These are rough approximations and not precise
            x_offset = 913200  # Approximate X offset for NYC
            y_offset = 120000  # Approximate Y offset for NYC
            x_scale = 364000   # Approximate X scale factor
            y_scale = 274000   # Approximate Y scale factor
            
            # Base lat/lon for NYC center
            base_lat = 40.7128
            base_lon = -74.0060
            
            df = df.copy()
            
            # Convert valid coordinates
            valid_mask = df['sign_x_coord'].notna() & df['sign_y_coord'].notna()
            
            if valid_mask.any():
                df.loc[valid_mask, 'longitude'] = base_lon + (df.loc[valid_mask, 'sign_x_coord'] - x_offset) / x_scale
                df.loc[valid_mask, 'latitude'] = base_lat + (df.loc[valid_mask, 'sign_y_coord'] - y_offset) / y_scale
                
                logging.info(f"Applied approximate coordinate conversion to {valid_mask.sum()} records")
            
            return df
            
        except Exception as e:
            logging.error(f"Error in approximate coordinate conversion: {e}")
            return df
    
    def find_nearby_violations(
        self, 
        lat: float, 
        lon: float, 
        radius_meters: int = 1000,
        start_date: str = None,
        end_date: str = None,
        limit: int = 100
    ) -> List[Dict]:
        """Find violations within radius of given coordinates and date range."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Use subquery to calculate distance and then filter
            query = """
                SELECT * FROM (
                    SELECT *,
                           (6371000 * acos(
                               cos(radians(?)) * cos(radians(latitude)) * 
                               cos(radians(longitude) - radians(?)) + 
                               sin(radians(?)) * sin(radians(latitude))
                           )) as distance_meters
                    FROM violations 
                    WHERE latitude IS NOT NULL 
                      AND longitude IS NOT NULL
            """
            params = [lat, lon, lat]
            
            # Add date filters if provided
            if start_date:
                query += " AND date(issue_date) >= date(?)"
                params.append(start_date)
            
            if end_date:
                query += " AND date(issue_date) <= date(?)"
                params.append(end_date)
            
            # Close subquery and add distance filter and ordering
            query += """
                ) WHERE distance_meters <= ?
                ORDER BY distance_meters ASC
                LIMIT ?
            """
            params.extend([radius_meters, limit])
            
            cursor.execute(query, params)
            columns = [description[0] for description in cursor.description]
            
            violations = []
            for row in cursor.fetchall():
                violation = dict(zip(columns, row))
                # Round distance for readability
                violation['distance_meters'] = round(violation['distance_meters'], 1)
                violations.append(violation)
            
            conn.close()
            return violations
            
        except Exception as e:
            logging.error(f"Error finding nearby violations: {e}")
            return []

    def get_data_status(self) -> Dict:
        """Get comprehensive data status for all data sources."""
        try:
            from datetime import datetime
            
            status = {
                "parking_signs": {
                    "total_count": 0,
                    "last_updated": "2023-12-31T00:00:00Z",
                    "coverage_areas": ["Manhattan", "Brooklyn", "Queens", "Bronx", "Staten Island"]
                },
                "meter_rates": {
                    "total_count": 0,
                    "last_updated": "2025-08-06T00:00:00Z",
                    "coverage_areas": ["Manhattan", "Brooklyn", "Queens", "Bronx", "Staten Island"]
                },
                "violations": {
                    "total_count": 0,
                    "last_updated": "2024-12-31T00:00:00Z",
                    "date_range": {
                        "start": "2020-01-01",
                        "end": "2024-12-31"
                    }
                }
            }
            
            # Get parking signs count
            if self.parking_signs_df is not None and not self.parking_signs_df.empty:
                status["parking_signs"]["total_count"] = len(self.parking_signs_df)
                status["parking_signs"]["last_updated"] = datetime.now().isoformat() + "Z"
            
            # Get meter zones count
            if self.meter_zones_df is not None and not self.meter_zones_df.empty:
                status["meter_rates"]["total_count"] = len(self.meter_zones_df)
                status["meter_rates"]["last_updated"] = datetime.now().isoformat() + "Z"
            
            # Get violations count from database
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                # Get total violations count
                cursor.execute("SELECT COUNT(*) FROM violations")
                violations_count = cursor.fetchone()[0]
                status["violations"]["total_count"] = violations_count
                
                # Get date range of violations
                cursor.execute("""
                    SELECT 
                        MIN(issue_date) as min_date,
                        MAX(issue_date) as max_date
                    FROM violations 
                    WHERE issue_date IS NOT NULL
                """)
                date_range = cursor.fetchone()
                
                if date_range and date_range[0] and date_range[1]:
                    status["violations"]["date_range"]["start"] = date_range[0]
                    status["violations"]["date_range"]["end"] = date_range[1]
                
                if violations_count > 0:
                    status["violations"]["last_updated"] = datetime.now().isoformat() + "Z"
                
                conn.close()
                
            except Exception as e:
                logging.warning(f"Could not get violations statistics: {e}")
            
            return status
            
        except Exception as e:
            logging.error(f"Error getting data status: {e}")
            # Return default status on error
            return {
                "parking_signs": {
                    "total_count": 0,
                    "last_updated": "2024-01-01T00:00:00Z",
                    "coverage_areas": ["Manhattan", "Brooklyn", "Queens", "Bronx", "Staten Island"]
                },
                "meter_rates": {
                    "total_count": 0,
                    "last_updated": "2024-01-01T00:00:00Z",
                    "coverage_areas": ["Manhattan", "Brooklyn", "Queens", "Bronx", "Staten Island"]
                },
                "violations": {
                    "total_count": 0,
                    "last_updated": "2024-01-01T00:00:00Z",
                    "date_range": {
                        "start": "2020-01-01",
                        "end": "2024-12-31"
                    }
                }
            } 