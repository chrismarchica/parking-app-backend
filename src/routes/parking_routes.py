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





 