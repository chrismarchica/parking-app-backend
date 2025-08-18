import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    PORT = int(os.getenv('PORT', 5000))
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    NYC_OPEN_DATA_API_KEY = os.getenv('NYC_OPEN_DATA_API_KEY', '')
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:3000')
    
    # NYC Open Data URLs
    PARKING_SIGNS_URL = "https://data.cityofnewyork.us/resource/nfid-uabd.json"  # Parking Regulation Locations and Signs
    METER_ZONES_URL = "https://data.cityofnewyork.us/resource/693u-uax6.json"  # Parking Meters Locations and Status
    VIOLATIONS_URL = "https://data.cityofnewyork.us/resource/pvqr-7yc4.json"  # Parking Violations 2024
    VIOLATIONS_2023_URL = "https://data.cityofnewyork.us/resource/869v-vr48.json"  # Parking Violations FY 2023
    
    # Database
    SQLITE_DB_PATH = "parking_data.db"
    
    # Data loading limits
    MAX_RECORDS_PER_REQUEST = 50000
    SEARCH_RADIUS_METERS = 100
    
    # Geocoding settings
    GEOCODING_API_URL = "https://geosearch.planninglabs.nyc/v2/search"  # NYC Planning Labs Geosearch v2
    MAX_VIOLATIONS_TO_LOAD = 10000  # Limit for performance
    GEOCODING_BATCH_SIZE = 100  # Process in batches to avoid rate limits 