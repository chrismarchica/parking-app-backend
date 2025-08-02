#!/usr/bin/env python3
"""
Simple test script to verify the Flask app works correctly with new structure
"""

import sys
import requests
import time
import subprocess
import json

def test_imports():
    """Test if all modules can be imported."""
    try:
        import env_config
        from src.config import Config
        from src.data.data_loader import DataLoader
        from src.routes.parking_routes import parking_bp
        from src.app import create_app
        from src.utils.helpers import validate_nyc_coordinates
        print("✅ All imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_app_creation():
    """Test if the Flask app can be created."""
    try:
        from src.app import create_app
        app = create_app()
        print("✅ Flask app created successfully")
        return True
    except Exception as e:
        print(f"❌ App creation error: {e}")
        return False

def test_config():
    """Test configuration loading."""
    try:
        import env_config
        from src.config import Config
        print(f"✅ Config loaded - Port: {Config.PORT}")
        print(f"✅ CORS Origins: {Config.CORS_ORIGINS}")
        return True
    except Exception as e:
        print(f"❌ Config error: {e}")
        return False

def test_utils():
    """Test utility functions."""
    try:
        from src.utils.helpers import validate_nyc_coordinates, calculate_distance
        
        # Test coordinate validation
        is_valid, msg = validate_nyc_coordinates(40.7589, -73.9851)
        if is_valid:
            print("✅ Coordinate validation working")
        else:
            print(f"❌ Coordinate validation failed: {msg}")
            return False
        
        # Test distance calculation
        distance = calculate_distance((40.7589, -73.9851), (40.7590, -73.9850))
        if distance > 0:
            print("✅ Distance calculation working")
        else:
            print("❌ Distance calculation failed")
            return False
            
        return True
    except Exception as e:
        print(f"❌ Utils error: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing NYC Parking API Setup (New Structure)\n")
    
    tests = [
        ("Import Test", test_imports),
        ("Config Test", test_config),
        ("Utils Test", test_utils),
        ("App Creation Test", test_app_creation),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"Running {test_name}...")
        result = test_func()
        results.append(result)
        print()
    
    success_count = sum(results)
    total_count = len(results)
    
    print(f"📊 Test Results: {success_count}/{total_count} passed")
    
    if success_count == total_count:
        print("🎉 All tests passed! The Flask app is ready to run.")
        print("\nTo start the server:")
        print("python main.py")
        print("\nOr:")
        print("python src/app.py")
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
        sys.exit(1)