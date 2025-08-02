# NYC Smart Parking API

A Flask backend for tracking parking availability using NYC Open Data.

## Features

- 🚗 **Parking Signs**: Find parking regulations within a radius
- 📊 **Violation Trends**: Analyze parking violations by borough and year  
- 💰 **Meter Rates**: Get parking meter zone information
- 🗄️ **Data Storage**: SQLite database for violation records

## Setup

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Environment Configuration**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Run the Application**
   ```bash
   python main.py
   ```
   
   Or run directly from src:
   ```bash
   python src/app.py
   ```

The API will be available at `http://localhost:5000`

## API Endpoints

### Health Check
```bash
curl http://localhost:5000/api/health
```

**Response:**
```json
{
  "status": "healthy",
  "message": "NYC Parking API is running"
}
```

### Parking Signs
```bash
curl "http://localhost:5000/api/parking-signs?lat=40.7589&lon=-73.9851&radius=100"
```

**Parameters:**
- **lat** (required): Latitude coordinate (40.4774 to 40.9176)
- **lon** (required): Longitude coordinate (-74.2591 to -73.7004)
- **radius** (optional): Search radius in meters (10-1000, default: 100)

**Example Response:**
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
        "distance_meters": 15.2,
        "street_name": "BROADWAY",
        "borough": "MANHATTAN"
      }
    ]
  }
}
```

### Meter Rates
```bash
curl "http://localhost:5000/api/meter-rate?lat=40.7589&lon=-73.9851"
```

**Parameters:**
- **lat** (required): Latitude coordinate (40.4774 to 40.9176)
- **lon** (required): Longitude coordinate (-74.2591 to -73.7004)

**Example Response:**
```json
{
  "query": {
    "latitude": 40.7589,
    "longitude": -73.9851
  },
  "result": {
    "meter_number": "1083067",
    "on_street": "BROADWAY",
    "meter_hours": "2HR Pas Mon-Sat 0800-2200",
    "borough": "Manhattan",
    "distance_meters": 245.6,
    "status": "Active"
  }
}
```

### Violation Trends
```bash
curl "http://localhost:5000/api/violation-trends?borough=MANHATTAN&year=2023"
```

**Parameters:**
- **borough** (optional): NYC borough name (MANHATTAN, BROOKLYN, QUEENS, BRONX, STATEN ISLAND)
- **year** (optional): Year to filter by (2010-2025)

**Example Response:**
```json
{
  "trends": [
    {
      "violation_type": "NO PARKING-STREET CLEANING",
      "count": 1250,
      "avg_fine": 65.00
    },
    {
      "violation_type": "EXPIRED METER",
      "count": 890,
      "avg_fine": 25.00
    }
  ],
  "total_violations": 2140,
  "filters": {
    "borough": "MANHATTAN",
    "year": 2023
  }
}
```

### Load Sample Data
```bash
curl -X POST http://localhost:5000/api/load-sample-data \
  -H "Content-Type: application/json" \
  -d '{"sample_size": 1000}'
```

**Parameters:**
- **sample_size** (optional): Number of sample records to generate (100-10000, default: 1000)

**Example Response:**
```json
{
  "message": "Successfully loaded 1000 sample violation records",
  "sample_size": 1000
}
```

### Debug Data Status
```bash
curl http://localhost:5000/api/debug/data-status
```

**Example Response:**
```json
{
  "parking_signs": {
    "loaded": true,
    "count": 1000,
    "columns": ["latitude", "longitude", "sign_description"],
    "sample": {
      "sign_description": "NO PARKING 8AM-6PM MON-FRI",
      "latitude": 40.7589,
      "longitude": -73.9851
    }
  },
  "meter_zones": {
    "loaded": true,
    "count": 15553,
    "columns": ["lat", "long", "meter_number", "on_street"],
    "sample": {
      "meter_number": "1083067",
      "on_street": "BROADWAY",
      "lat": 40.7854736906031,
      "long": -73.9785542783786
    }
  },
  "url_tests": {
    "parking_signs": {
      "accessible": true,
      "status_code": 200
    },
    "meter_zones": {
      "accessible": true,
      "status_code": 200
    }
  }
}
```

## Data Sources

- **Parking Signs**: [NYC Open Data - Parking Regulation Locations](https://data.cityofnewyork.us/Transportation/Parking-Regulation-Locations-and-Signs/nfid-uabd)
- **Meter Zones**: [NYC Open Data - Parking Meter Zones](https://data.cityofnewyork.us/Transportation/Parking-Meter-Zones/r5z5-qqjr)
- **Violations**: Sample data generated for demonstration

## NYC Coordinate Bounds

- **Latitude**: 40.4774 to 40.9176
- **Longitude**: -74.2591 to -73.7004

## Frontend Integration

This API is designed to work with a Next.js frontend hosted at `http://localhost:3000`. CORS is pre-configured for this setup.

Example frontend fetch:
```javascript
const response = await fetch('http://localhost:5000/api/parking-signs?lat=40.7589&lon=-73.9851');
const data = await response.json();
```

## Error Handling

The API includes comprehensive error handling with appropriate HTTP status codes:

### 400 Bad Request
```bash
curl "http://localhost:5000/api/parking-signs?lat=invalid&lon=-73.9851"
```
```json
{
  "error": "Invalid parameter value: could not convert string to float: 'invalid'"
}
```

### 400 Validation Errors
```bash
curl "http://localhost:5000/api/parking-signs?lat=50.0&lon=-73.9851"
```
```json
{
  "error": "Latitude must be within NYC bounds (40.4774 to 40.9176)"
}
```

### 500 Internal Server Error
When data loading fails, the API gracefully falls back to sample data and continues operating.

## Testing

### Quick Test Script
```bash
# Test all endpoints
curl http://localhost:5000/api/health
curl "http://localhost:5000/api/meter-rate?lat=40.7589&lon=-73.9851"
curl "http://localhost:5000/api/parking-signs?lat=40.7589&lon=-73.9851&radius=200"
curl "http://localhost:5000/api/violation-trends?borough=MANHATTAN"
curl http://localhost:5000/api/debug/data-status
```

### Load Sample Data for Testing
```bash
curl -X POST http://localhost:5000/api/load-sample-data \
  -H "Content-Type: application/json" \
  -d '{"sample_size": 5000}'
```

### Test Different Locations
```bash
# Times Square
curl "http://localhost:5000/api/parking-signs?lat=40.7589&lon=-73.9851&radius=100"

# Lower Manhattan
curl "http://localhost:5000/api/parking-signs?lat=40.7074&lon=-74.0113&radius=100"

# Brooklyn
curl "http://localhost:5000/api/parking-signs?lat=40.7182&lon=-73.9581&radius=100"
```