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
    
    # Database
    SQLITE_DB_PATH = "parking_data.db"
    
    # Data loading limits
    MAX_RECORDS_PER_REQUEST = 50000
    SEARCH_RADIUS_METERS = 100 