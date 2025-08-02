# 🚀 NYC Smart Parking API - Quick Start Guide

## What We Built

A complete Flask backend for smart parking availability tracking using NYC Open Data with the following features:

### 📁 Project Structure
```
parking_app/
├── main.py              # 🚀 Main entry point
├── src/                 # 📁 Source code
│   ├── app.py          # Flask application
│   ├── config.py       # Configuration
│   ├── data/           # Data processing
│   │   ├── data_loader.py
│   │   └── __init__.py
│   ├── routes/         # API endpoints
│   │   ├── parking_routes.py
│   │   └── __init__.py
│   └── utils/          # 🛠️ Utility functions
│       ├── helpers.py
│       └── __init__.py
├── requirements.txt     # Dependencies
├── test_app.py         # Test script
├── README.md           # Full documentation
├── startup_guide.md    # This guide
├── .gitignore          # Git ignore rules
└── env_config.py       # Environment setup
```

### 🛠️ Core Features

1. **Data Loading**: Automatic loading of NYC parking signs and meter zones
2. **SQLite Database**: Storage for parking violation data
3. **CORS Enabled**: Ready for Next.js frontend at localhost:3000
4. **Modular Design**: Clean separation with blueprints
5. **Error Handling**: Comprehensive validation and error responses

## 🏃‍♂️ Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Test Setup (Optional)
```bash
python test_app.py
```

### 3. Start the Server
```bash
python main.py
```

Or run directly from src:
```bash
python src/app.py
```

The API will be available at `http://localhost:5000`

## 📡 API Endpoints

### Health Check
```
GET http://localhost:5000/api/health
```

### Find Parking Signs Near Location
```
GET http://localhost:5000/api/parking-signs?lat=40.7589&lon=-73.9851&radius=100
```

**Parameters:**
- `lat` (required): Latitude (40.4774 to 40.9176)
- `lon` (required): Longitude (-74.2591 to -73.7004)
- `radius` (optional): Search radius in meters (10-1000, default: 100)

**Response:**
```json
{
  "query": {
    "latitude": 40.7589,
    "longitude": -73.9851,
    "radius_meters": 100
  },
  "results": {
    "count": 5,
    "signs": [
      {
        "sign_description": "NO PARKING 8AM-6PM MON-FRI",
        "latitude": 40.7590,
        "longitude": -73.9850,
        "distance_meters": 15.2
      }
    ]
  }
}
```

### Get Violation Trends
```
GET http://localhost:5000/api/violation-trends?borough=MANHATTAN&year=2023
```

**Parameters:**
- `borough` (optional): MANHATTAN, BROOKLYN, QUEENS, BRONX, STATEN ISLAND
- `year` (optional): Year to filter by (2010-2025)

### Find Nearest Meter Zone
```
GET http://localhost:5000/api/meter-rate?lat=40.7589&lon=-73.9851
```

### Load Sample Data (for Testing)
```
POST http://localhost:5000/api/load-sample-data
Content-Type: application/json

{
  "sample_size": 1000
}
```

## 🌐 Frontend Integration Example

```javascript
// Example Next.js/React code
const fetchParkingSigns = async (lat, lon) => {
  try {
    const response = await fetch(
      `http://localhost:5000/api/parking-signs?lat=${lat}&lon=${lon}&radius=200`
    );
    
    if (!response.ok) {
      throw new Error('Failed to fetch parking signs');
    }
    
    const data = await response.json();
    return data.results.signs;
  } catch (error) {
    console.error('Error fetching parking signs:', error);
    return [];
  }
};

// Usage in component
useEffect(() => {
  fetchParkingSigns(40.7589, -73.9851)
    .then(signs => {
      console.log('Found parking signs:', signs);
      // Update your map or UI with the signs
    });
}, []);
```

## 🔧 Configuration

The app uses environment-based configuration through `env_config.py`:

- **PORT**: Server port (default: 5000)
- **FLASK_ENV**: Environment mode (development/production)
- **CORS_ORIGINS**: Allowed origins for CORS (default: http://localhost:3000)
- **NYC_OPEN_DATA_API_KEY**: Optional API key for NYC Open Data

## 🗃️ Data Sources

1. **Parking Signs**: [NYC Open Data - Parking Regulation Locations](https://data.cityofnewyork.us/Transportation/Parking-Regulation-Locations-and-Signs/nfid-uabd)
2. **Meter Zones**: [NYC Open Data - Parking Meter Zones](https://data.cityofnewyork.us/Transportation/Parking-Meter-Zones/r5z5-qqjr)
3. **Violations**: Sample data generated for demonstration

## 🚨 Error Handling

The API includes comprehensive error handling:

- **400 Bad Request**: Invalid parameters or missing required fields
- **500 Internal Server Error**: Server-side issues with detailed logging
- **Coordinate Validation**: Ensures lat/lon are within NYC bounds
- **Data Validation**: Checks for proper data types and ranges

## 🔍 Testing the API

You can test the endpoints using:

1. **Browser**: Visit `http://localhost:5000/api/health`
2. **curl**: 
   ```bash
   curl "http://localhost:5000/api/parking-signs?lat=40.7589&lon=-73.9851"
   ```
3. **Postman**: Import the endpoints for interactive testing
4. **Python requests**:
   ```python
   import requests
   response = requests.get('http://localhost:5000/api/health')
   print(response.json())
   ```

## 📋 Next Steps for Frontend

When building your Next.js frontend, consider:

1. **Map Integration**: Use Leaflet or Google Maps to display parking signs
2. **Real-time Updates**: Implement periodic API calls for fresh data
3. **User Location**: Use browser geolocation to center the map
4. **Filtering**: Add filters for violation types, time ranges, etc.
5. **Caching**: Implement client-side caching for better performance

## 🐛 Troubleshooting

### Common Issues:

1. **Import Errors**: Make sure all dependencies are installed with `pip install -r requirements.txt`
2. **Port Already in Use**: Change the PORT in `env_config.py`
3. **CORS Issues**: Verify CORS_ORIGINS matches your frontend URL
4. **Data Loading Failures**: Check internet connection for NYC Open Data access

### Logs:
The application logs important information to help with debugging. Check the console output when starting the server.

---

🎉 **Your NYC Smart Parking API is ready!** Start the server with `python app.py` and begin building your Next.js frontend to create an interactive parking map.