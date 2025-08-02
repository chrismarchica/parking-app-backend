from flask import Flask
from flask_cors import CORS
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import env_config  # Load environment variables
from src.config import Config
from src.routes.parking_routes import parking_bp
from src.data.data_loader import DataLoader
import logging

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Setup CORS
    CORS(app, origins=app.config['CORS_ORIGINS'])
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Register blueprints with /api prefix
    app.register_blueprint(parking_bp, url_prefix='/api')
    
    # Initialize data loader
    with app.app_context():
        data_loader = DataLoader()
        app.data_loader = data_loader
        
        # Load initial data
        try:
            logging.info("Loading parking signs data...")
            data_loader.load_parking_signs()
            logging.info("Loading meter zones data...")
            data_loader.load_meter_zones()
            logging.info("Data loading completed successfully")
        except Exception as e:
            logging.error(f"Error loading data: {e}")
    
    @app.route('/api/health')
    def health_check():
        return {'status': 'healthy', 'message': 'NYC Parking API is running'}
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(
        host='0.0.0.0',
        port=app.config['PORT'],
        debug=app.config['FLASK_ENV'] == 'development'
    ) 