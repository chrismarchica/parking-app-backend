#!/usr/bin/env python3
"""
Main entry point for NYC Smart Parking API
"""
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.app import create_app

if __name__ == '__main__':
    app = create_app()
    app.run(
        host='0.0.0.0',
        port=app.config['PORT'],
        debug=app.config['FLASK_ENV'] == 'development'
    ) 