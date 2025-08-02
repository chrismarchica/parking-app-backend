"""
Utility functions for NYC Smart Parking API
"""
import logging
from typing import Dict, List, Optional, Tuple
from geopy.distance import geodesic

def validate_nyc_coordinates(lat: float, lon: float) -> Tuple[bool, str]:
    """
    Validate if coordinates are within NYC bounds.
    
    Args:
        lat: Latitude coordinate
        lon: Longitude coordinate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    nyc_bounds = {
        'lat_min': 40.4774, 'lat_max': 40.9176,
        'lon_min': -74.2591, 'lon_max': -73.7004
    }
    
    if not (nyc_bounds['lat_min'] <= lat <= nyc_bounds['lat_max']):
        return False, f"Latitude must be within NYC bounds ({nyc_bounds['lat_min']} to {nyc_bounds['lat_max']})"
    
    if not (nyc_bounds['lon_min'] <= lon <= nyc_bounds['lon_max']):
        return False, f"Longitude must be within NYC bounds ({nyc_bounds['lon_min']} to {nyc_bounds['lon_max']})"
    
    return True, ""

def calculate_distance(point1: Tuple[float, float], point2: Tuple[float, float]) -> float:
    """
    Calculate distance between two points using geodesic distance.
    
    Args:
        point1: (lat, lon) tuple for first point
        point2: (lat, lon) tuple for second point
        
    Returns:
        Distance in meters
    """
    return geodesic(point1, point2).meters

def format_coordinate_response(lat: float, lon: float, radius: int = None) -> Dict:
    """
    Format a standard coordinate query response.
    
    Args:
        lat: Latitude coordinate
        lon: Longitude coordinate
        radius: Optional search radius
        
    Returns:
        Formatted response dictionary
    """
    response = {
        'query': {
            'latitude': lat,
            'longitude': lon
        }
    }
    
    if radius is not None:
        response['query']['radius_meters'] = radius
        
    return response

def log_api_request(endpoint: str, params: Dict, user_agent: str = None):
    """
    Log API request details for debugging.
    
    Args:
        endpoint: API endpoint being called
        params: Query parameters
        user_agent: Optional user agent string
    """
    logging.info(f"API Request: {endpoint}")
    logging.info(f"Parameters: {params}")
    if user_agent:
        logging.info(f"User Agent: {user_agent}")

def sanitize_dataframe_columns(df_columns: List[str]) -> List[str]:
    """
    Sanitize column names for safe JSON serialization.
    
    Args:
        df_columns: List of column names from pandas DataFrame
        
    Returns:
        List of sanitized column names
    """
    sanitized = []
    for col in df_columns:
        # Remove problematic characters and replace with underscores
        sanitized_col = col.replace(':', '_').replace('@', '_').replace(' ', '_')
        sanitized.append(sanitized_col)
    return sanitized 