# Pricing System Setup Guide

## Pricing Rules

- **Base Fare**: ₹30
- **Price per km**: ₹8
- **Price per kg**: ₹5
- **Extra stop charge**: ₹15 per stop (after first stop)

## Google Distance Matrix API Setup

### 1. Get API Key

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable "Distance Matrix API"
4. Create credentials (API Key)
5. Copy your API key

### 2. Configure API Key

**Option 1: Environment Variable (Recommended)**
```bash
export GOOGLE_API_KEY="your_api_key_here"
```

**Option 2: Create .env file**
```bash
# Copy the example file
cp .env.example .env

# Edit .env and add your API key
GOOGLE_API_KEY=your_api_key_here
```

**Option 3: Direct in app.py (Not Recommended)**
Edit `app.py` and set:
```python
GOOGLE_API_KEY = 'your_api_key_here'
```

### 3. Fallback Behavior

If no API key is configured, the system will:
- Use estimated distance (5km per segment)
- Still calculate prices correctly
- Show "estimated" in the UI

## Price Calculation

The system calculates:
1. **Base Fare**: ₹30 (fixed)
2. **Distance Cost**: Total distance × ₹8
3. **Weight Cost**: Weight (kg) × ₹5
4. **Extra Stop Cost**: (Number of stops - 1) × ₹15
5. **Total**: Sum of all above

## API Endpoint

### POST `/api/calculate-price`

**Request:**
```json
{
    "pickup_address": "123 Main St, City",
    "stops": [
        {
            "stop_number": 1,
            "drop_address": "456 Oak Ave, City",
            "receiver_name": "John Doe",
            "receiver_phone": "1234567890"
        }
    ],
    "weight": 2.5
}
```

**Response:**
```json
{
    "success": true,
    "price_breakdown": {
        "base_fare": 30,
        "distance": 12.5,
        "distance_cost": 100,
        "weight": 2.5,
        "weight_cost": 12.5,
        "num_stops": 2,
        "extra_stops": 1,
        "extra_stop_cost": 15,
        "total": 157.5
    }
}
```

## Frontend Features

- **Live Price Updates**: Price recalculates automatically when:
  - Weight changes
  - Stops are added/removed
  - Addresses are modified

- **Price Breakdown**: Shows detailed breakdown of:
  - Base fare
  - Distance cost
  - Weight cost
  - Extra stop charges
  - Total price

## Testing Without API Key

The system works without an API key using estimated distances:
- Each segment estimated as 5km
- Prices still calculated correctly
- Suitable for development/testing

