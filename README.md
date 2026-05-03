# Fuel Route Optimizer API

A Django REST API that calculates the optimal fuel stops and total fuel cost for a driving route between two US cities.

---

##  Key Features

*  Single routing API call (efficient)
*  Smart fuel stop selection based on vehicle range (500 miles)
*  Uses real fuel price dataset (8,000+ stations)
*  No database required (CSV-based)
*  Fast response using caching
*  Clean modular backend architecture

---

##  How It Works

```
POST /api/route/
  │
  ├─ 1. Validate input (start, end)
  ├─ 2. Geocode cities → (lat, lon) [OpenRouteService]
  ├─ 3. Fetch route (distance + geometry) [OpenRouteService]
  ├─ 4. Detect states along route (no extra API calls)
  ├─ 5. Divide route into 500-mile segments
  ├─ 6. Select cheapest fuel station per segment
  ├─ 7. Calculate total fuel cost
  └─ 8. Return JSON response
```

---

##  Constraints

* Vehicle range: **500 miles**
* Fuel efficiency: **10 miles per gallon**
* Fuel stops selected from CSV dataset
* Only **1 routing API call per request**

---

##  Project Structure

```
fuel_route_spotterAI/
├── manage.py
├── requirements.txt
├── .env.example
├── README.md
│
├── data/
│   └── fuel_prices.csv
│
├── fuel_route/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
│
└── api/
    ├── views.py
    ├── urls.py
    ├── serializers.py
    └── services/
        ├── geocoding.py     # Uses OpenRouteService (NOT Nominatim)
        ├── routing.py
        ├── us_states.py
        ├── fuel.py
        └── cost.py
```

---

## ⚡ Quick Start

### 1. Setup project

```bash
cd fuel_route_spotterAI
python -m venv venv
source venv/bin/activate   # Mac/Linux
venv\Scripts\activate      # Windows
```

---

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

---

### 3. Setup environment variables

```bash
cp .env.example .env
```

Add your API key:

```
ORS_API_KEY=your_key_here
```

Get it free: https://openrouteservice.org/dev/#/signup

---

### 4. Run server

```bash
python manage.py runserver
```

---

##  API Endpoint

### `POST /api/route/`

#### Request

```json
{
  "start": "Chicago, IL",
  "end": "Houston, TX"
}
```

---

#### Response

```json
{
  "start": "Chicago, IL",
  "end": "Houston, TX",
  "distance": 1080.9,
  "fuel_stops": [
    {"location": "QUIKTRIP #605, Saint Louis, MO", "price": 2.899},
    {"location": "7-ELEVEN #218, Harrold, TX", "price": 2.6873}
  ],
  "total_cost": 279.31
}
```

---

##  Example Usage

```bash
curl -X POST http://127.0.0.1:8000/api/route/ \
  -H "Content-Type: application/json" \
  -d '{"start": "New York, NY", "end": "Miami, FL"}'
```

---

##  Design Decisions

| Decision                                 | Reason                              |
| ---------------------------------------- | ----------------------------------- |
| OpenRouteService for routing + geocoding | Reliable, avoids Nominatim blocking |
| Segment-based fuel logic                 | Matches real-world fuel constraints |
| Bounding-box state detection             | No extra API calls                  |
| Pandas + caching                         | Fast CSV processing                 |
| No database                              | Simpler and faster                  |

---

##  Assumptions

* Vehicle starts with a **full tank**
* Fuel is filled completely at each stop
* State detection is approximate (bounding boxes)
* Fuel stations are filtered by state (not exact coordinates)

---

##  Possible Improvements

* Use exact geo-coordinates for fuel stations
* Implement true greedy optimization with distance awareness
* Add Redis caching for routes
* Improve state detection using GeoJSON

---

##  Dependencies

* Django
* Django REST Framework
* Requests
* Pandas
* python-dotenv

---

##  Status

✔ Fully functional
✔ Tested with multiple routes
✔ Handles edge cases
✔ Ready for submission

---
