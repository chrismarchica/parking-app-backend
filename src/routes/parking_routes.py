from flask import Blueprint, request, jsonify, current_app
import logging
from src.utils.helpers import validate_nyc_coordinates, format_coordinate_response, log_api_request

parking_bp = Blueprint('parking', __name__)

@parking_bp.route('/parking-signs')
def get_parking_signs():
    """
    Get parking signs within a radius of specified coordinates.
    
    Query Parameters:
    - lat (float, required): Latitude
    - lon (float, required): Longitude  
    - radius (int, optional): Search radius in meters (default: 100)
    
    Returns:
    - JSON array of parking signs with details and distances
    """
    try:
        # Get query parameters
        lat = request.args.get('lat', type=float)
        lon = request.args.get('lon', type=float)
        radius = request.args.get('radius', type=int, default=100)
        
        # Validate required parameters
        if lat is None or lon is None:
            return jsonify({
                'error': 'Missing required parameters: lat and lon',
                'example': '/api/parking-signs?lat=40.7589&lon=-73.9851'
            }), 400
        
        # Validate coordinates using utility function
        is_valid, error_msg = validate_nyc_coordinates(lat, lon)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        if not (10 <= radius <= 1000):
            return jsonify({
                'error': 'Radius must be between 10 and 1000 meters'
            }), 400
        
        # Log the API request
        log_api_request('/parking-signs', {'lat': lat, 'lon': lon, 'radius': radius})
        
        # Get data from data loader
        data_loader = current_app.data_loader
        nearby_signs = data_loader.find_nearby_parking_signs(lat, lon, radius)
        
        # Format response using utility function
        response = format_coordinate_response(lat, lon, radius)
        response['results'] = {
            'count': len(nearby_signs),
            'signs': nearby_signs
        }
        
        return jsonify(response)
        
    except ValueError as e:
        return jsonify({
            'error': f'Invalid parameter value: {str(e)}'
        }), 400
    except Exception as e:
        logging.error(f"Error in get_parking_signs: {e}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'Unable to fetch parking signs data'
        }), 500


@parking_bp.route('/violation-trends')
def get_violation_trends():
    """
    Get parking violation trends by borough and year.
    
    Query Parameters:
    - borough (str, optional): NYC borough name
    - year (int, optional): Year to filter by
    
    Returns:
    - JSON object with violation trends and statistics
    """
    try:
        # Get query parameters
        borough = request.args.get('borough', type=str)
        year = request.args.get('year', type=int)
        
        # Validate borough if provided
        valid_boroughs = ['MANHATTAN', 'BROOKLYN', 'QUEENS', 'BRONX', 'STATEN ISLAND']
        if borough and borough.upper() not in valid_boroughs:
            return jsonify({
                'error': f'Invalid borough. Must be one of: {", ".join(valid_boroughs)}'
            }), 400
        
        # Validate year if provided
        if year and not (2010 <= year <= 2025):
            return jsonify({
                'error': 'Year must be between 2010 and 2025'
            }), 400
        
        # Log the API request
        log_api_request('/violation-trends', {'borough': borough, 'year': year})
        
        # Get data from data loader
        data_loader = current_app.data_loader
        trends_data = data_loader.get_violation_trends(
            borough=borough.upper() if borough else None,
            year=year
        )
        
        return jsonify(trends_data)
        
    except Exception as e:
        logging.error(f"Error in get_violation_trends: {e}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'Unable to fetch violation trends data'
        }), 500


@parking_bp.route('/meter-rate')
def get_meter_rate():
    """
    Get nearest parking meter zone and rate information.
    
    Query Parameters:
    - lat (float, required): Latitude
    - lon (float, required): Longitude
    
    Returns:
    - JSON object with meter zone information and rates
    """
    try:
        # Get query parameters
        lat = request.args.get('lat', type=float)
        lon = request.args.get('lon', type=float)
        
        # Validate required parameters
        if lat is None or lon is None:
            return jsonify({
                'error': 'Missing required parameters: lat and lon',
                'example': '/api/meter-rate?lat=40.7589&lon=-73.9851'
            }), 400
        
        # Validate coordinates using utility function
        is_valid, error_msg = validate_nyc_coordinates(lat, lon)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        # Log the API request
        log_api_request('/meter-rate', {'lat': lat, 'lon': lon})
        
        # Get data from data loader
        data_loader = current_app.data_loader
        
        # Debug: Check if we have meter data loaded
        if data_loader.meter_zones_df is None:
            logging.warning("Meter zones dataframe is None")
        elif data_loader.meter_zones_df.empty:
            logging.warning("Meter zones dataframe is empty")
        else:
            logging.info(f"Meter zones dataframe has {len(data_loader.meter_zones_df)} rows")
            logging.info(f"Columns: {list(data_loader.meter_zones_df.columns)}")
            if len(data_loader.meter_zones_df) > 0:
                sample_row = data_loader.meter_zones_df.iloc[0]
                logging.info(f"Sample row: {sample_row.to_dict()}")
        
        meter_zone = data_loader.find_nearest_meter_zone(lat, lon)
        
        if meter_zone is None:
            return jsonify({
                'query': {
                    'latitude': lat,
                    'longitude': lon
                },
                'result': None,
                'message': 'No meter zones found near this location'
            })
        
        # Format response using utility function
        response = format_coordinate_response(lat, lon)
        response['result'] = meter_zone
        
        return jsonify(response)
        
    except ValueError as e:
        return jsonify({
            'error': f'Invalid parameter value: {str(e)}'
        }), 400
    except Exception as e:
        logging.error(f"Error in get_meter_rate: {e}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'Unable to fetch meter rate data'
        }), 500


@parking_bp.route('/data-status')
def get_data_status():
    """
    Get comprehensive data status for all data sources.
    
    Returns:
    - JSON object with statistics for parking signs, meter rates, and violations
    """
    try:
        # Log the API request
        log_api_request('/data-status', {})
        
        # Get data status from data loader
        data_loader = current_app.data_loader
        status = data_loader.get_data_status()
        
        return jsonify(status)
        
    except Exception as e:
        logging.error(f"Error in get_data_status: {e}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'Unable to fetch data status'
        }), 500


@parking_bp.route('/load-real-violations', methods=['POST'])
def load_real_violations():
    """
    Load real violation data from NYC Open Data.
    
    Request Body:
    - limit (int, optional): Number of records to load (default: 10000, max: 50000)
    
    Returns:
    - JSON object with success message and record count
    """
    try:
        # Log the API request
        log_api_request('/load-real-violations', {})
        
        # Get limit from request
        data = request.get_json() or {}
        limit = data.get('limit', 10000)
        
        # Validate limit
        if not isinstance(limit, int) or limit < 100 or limit > 50000:
            return jsonify({
                'error': 'Invalid limit',
                'message': 'limit must be an integer between 100 and 50000'
            }), 400
        
        # Load real violations data
        data_loader = current_app.data_loader
        success = data_loader.load_real_violations(limit)
        
        if not success:
            return jsonify({
                'error': 'Failed to load violations data',
                'message': 'Unable to fetch or process violations from NYC Open Data'
            }), 500
        
        # Get actual count from database
        import sqlite3
        conn = sqlite3.connect(data_loader.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM violations")
        actual_count = cursor.fetchone()[0]
        conn.close()
        
        return jsonify({
            'message': f'Successfully loaded real violation data',
            'requested_limit': limit,
            'total_violations_in_db': actual_count,
            'data_source': 'NYC Open Data'
        })
        
    except Exception as e:
        logging.error(f"Error in load_real_violations: {e}")
        return jsonify({
            'error': 'Internal server error',
            'message': f'Unable to load real violations data: {str(e)}'
        }), 500


@parking_bp.route('/load-sample-data', methods=['POST'])
def load_sample_data():
    """
    Load sample violation data for demonstration.
    
    Request Body:
    - sample_size (int, optional): Number of sample records to generate (default: 1000)
    
    Returns:
    - JSON object with success message and sample size
    """
    try:
        # Log the API request
        log_api_request('/load-sample-data', {})
        
        # Get sample size from request
        data = request.get_json() or {}
        sample_size = data.get('sample_size', 1000)
        
        # Validate sample size
        if not isinstance(sample_size, int) or sample_size < 100 or sample_size > 10000:
            return jsonify({
                'error': 'Invalid sample_size',
                'message': 'sample_size must be an integer between 100 and 10000'
            }), 400
        
        # Load sample data
        data_loader = current_app.data_loader
        data_loader.load_sample_violations(sample_size)
        
        return jsonify({
            'message': f'Successfully loaded {sample_size} sample violation records',
            'sample_size': sample_size
        })
        
    except Exception as e:
        logging.error(f"Error in load_sample_data: {e}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'Unable to load sample data'
        }), 500


@parking_bp.route('/reload-parking-signs', methods=['POST'])
def reload_parking_signs():
    """
    Reload parking signs data (or create sample data if loading fails).
    
    Returns:
    - JSON object with success message and sign count
    """
    try:
        # Log the API request
        log_api_request('/reload-parking-signs', {})
        
        # Reload parking signs data
        data_loader = current_app.data_loader
        success = data_loader.load_parking_signs()
        
        # Debug information
        df_status = "None" if data_loader.parking_signs_df is None else f"DataFrame with {len(data_loader.parking_signs_df)} rows"
        
        # If no data after loading, force sample data creation
        if data_loader.parking_signs_df is None or data_loader.parking_signs_df.empty:
            logging.info("Forcing sample parking signs creation...")
            data_loader._create_sample_parking_signs()
        
        signs_count = len(data_loader.parking_signs_df) if data_loader.parking_signs_df is not None else 0
        
        return jsonify({
            'message': f'Parking signs reloaded. Count: {signs_count}',
            'success': success,
            'signs_count': signs_count,
            'debug_info': df_status
        })
        
    except Exception as e:
        logging.error(f"Error in reload_parking_signs: {e}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'Unable to reload parking signs'
        }), 500


@parking_bp.route('/violations')
def get_violations():
    """
    Get parking violations within a radius of specified coordinates and date range.
    
    Query Parameters:
    - lat (float, required): Latitude
    - lon (float, required): Longitude  
    - radius (int, optional): Search radius in meters (default: 1000)
    - start_date (string, optional): Start date filter (YYYY-MM-DD format)
    - end_date (string, optional): End date filter (YYYY-MM-DD format)
    - limit (int, optional): Maximum number of results (default: 100, max: 1000)
    
    Returns:
    - JSON array of parking violations with details and distances
    """
    try:
        # Get query parameters
        lat = request.args.get('lat', type=float)
        lon = request.args.get('lon', type=float)
        radius = request.args.get('radius', type=int, default=1000)
        start_date = request.args.get('start_date', type=str)
        end_date = request.args.get('end_date', type=str)
        limit = request.args.get('limit', type=int, default=100)
        
        # Validate required parameters
        if lat is None or lon is None:
            return jsonify({
                'error': 'Missing required parameters: lat and lon',
                'example': '/api/violations?lat=40.7589&lon=-73.9851&radius=1000'
            }), 400
        
        # Validate coordinates using utility function
        is_valid, error_msg = validate_nyc_coordinates(lat, lon)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        # Validate radius
        if not (10 <= radius <= 5000):
            return jsonify({
                'error': 'Radius must be between 10 and 5000 meters'
            }), 400
        
        # Validate limit
        if not (1 <= limit <= 1000):
            return jsonify({
                'error': 'Limit must be between 1 and 1000'
            }), 400
        
        # Validate date formats if provided
        if start_date:
            try:
                from datetime import datetime
                datetime.strptime(start_date, '%Y-%m-%d')
            except ValueError:
                return jsonify({
                    'error': 'Invalid start_date format. Use YYYY-MM-DD'
                }), 400
        
        if end_date:
            try:
                from datetime import datetime
                datetime.strptime(end_date, '%Y-%m-%d')
            except ValueError:
                return jsonify({
                    'error': 'Invalid end_date format. Use YYYY-MM-DD'
                }), 400
        
        # Log the API request
        log_api_request('/violations', {
            'lat': lat, 'lon': lon, 'radius': radius,
            'start_date': start_date, 'end_date': end_date, 'limit': limit
        })
        
        # Get data from data loader
        data_loader = current_app.data_loader
        nearby_violations = data_loader.find_nearby_violations(
            lat, lon, radius, start_date, end_date, limit
        )
        
        # Format response using utility function
        response = format_coordinate_response(lat, lon, radius)
        response['filters'] = {
            'start_date': start_date,
            'end_date': end_date,
            'limit': limit
        }
        response['results'] = {
            'count': len(nearby_violations),
            'violations': nearby_violations
        }
        
        return jsonify(response)
        
    except ValueError as e:
        return jsonify({
            'error': f'Invalid parameter value: {str(e)}'
        }), 400
    except Exception as e:
        logging.error(f"Error in get_violations: {e}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'Unable to fetch violations data'
        }), 500


@parking_bp.route('/debug/test-nyc-api', methods=['GET'])
def test_nyc_api():
    """
    Test the NYC Open Data API endpoints directly.
    
    Returns:
    - JSON object with API test results
    """
    try:
        import requests
        from src.config import Config
        
        results = {}
        
        # Test parking signs API
        try:
            url = f"{Config.PARKING_SIGNS_URL}?$limit=10"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json',
            }
            response = requests.get(url, timeout=30, headers=headers)
            
            results['parking_signs'] = {
                'url': url,
                'status_code': response.status_code,
                'headers': dict(response.headers),
                'data_length': len(response.json()) if response.status_code == 200 else 0,
                'raw_response_length': len(response.content),
                'error': None
            }
            
            if response.status_code == 200:
                data = response.json()
                if data:
                    results['parking_signs']['sample_record'] = data[0] if len(data) > 0 else "No records"
                    results['parking_signs']['columns'] = list(data[0].keys()) if len(data) > 0 else []
            
        except Exception as e:
            results['parking_signs'] = {
                'error': str(e),
                'url': f"{Config.PARKING_SIGNS_URL}?$limit=10"
            }
        
        # Test meter zones API
        try:
            url = f"{Config.METER_ZONES_URL}?$limit=10"
            response = requests.get(url, timeout=30)
            
            results['meter_zones'] = {
                'url': url,
                'status_code': response.status_code,
                'data_length': len(response.json()) if response.status_code == 200 else 0,
                'error': None
            }
            
        except Exception as e:
            results['meter_zones'] = {
                'error': str(e),
                'url': f"{Config.METER_ZONES_URL}?$limit=10"
            }
        
        return jsonify(results)
        
    except Exception as e:
        logging.error(f"Error in test_nyc_api: {e}")
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500





 