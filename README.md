# Weather-Aware Truck Routing

Pick the safest truck route by weather risk, load weight and travel time.
React + TypeScript frontend (`frontend/`) and a Django REST backend (`backend/`).

## Run the whole app (two terminals)

Prerequisites: Python 3.11+, Node 20+, and a free Mapbox token (see [API keys](#api-keys)).

**Terminal 1: backend** (http://127.0.0.1:8000)

```powershell
cd backend
python -m venv .venv
.venv\Scripts\activate            # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env            # macOS/Linux: cp .env.example .env
# edit backend/.env and paste your MAPBOX_TOKEN
python manage.py runserver
```

**Terminal 2: frontend** (http://localhost:5173)

```powershell
cd frontend
npm install
npm run dev
```

Open http://localhost:5173. In development Vite proxies `/api` to Django, so no frontend env file is needed. For a deployed build set `VITE_API_BASE_URL` (see `frontend/.env.example`) and add the frontend URL to `CORS_ALLOWED_ORIGINS` in the backend `.env`.

## Frontend

```
frontend/src/
  api/routesApi.ts          typed fetch client, maps 400/422/502 to friendly errors
  hooks/useRouteAnalysis.ts loading / error / data state, cancels stale requests
  types/api.ts              TypeScript types mirroring the API response
  utils/                    risk colours, date / distance formatting
  components/
    RouteForm.tsx           origin, destination, departure, load + validation
    ResultsPanel.tsx        recommendation banner + warnings + route cards + table
    RouteCard.tsx           one route: distance, time, ETA, Severe/High miles, avg risk
    CheckpointTable.tsx     checkpoints of the selected route
    map/MapView.tsx         Leaflet map (canvas renderer)
    map/RouteLines.tsx      the 3 routes; click to select
    map/CheckpointMarkers.tsx  risk-coloured dots with weather popup
    map/HeatmapLayer.tsx    one persistent leaflet.heat layer, slider only swaps data
    map/HeatmapControls.tsx 0-48 h slider, time label, legend, show/hide
```

Why the slider is smooth: the backend sends all 49 hourly frames in the single analyze response, so moving the slider makes no network request. It only swaps the data of one existing heat layer.

Run `npm run build` for a type-checked production build and `npm run lint` for lint.

## How it works

One endpoint does everything: `POST /api/routes/analyze`

```
geocode origin/destination  (Mapbox)
   -> 3 alternative routes   (Mapbox Directions)
   -> checkpoints every 10/25/50 mi + ETA at each      services/sampling.py
   -> forecast at each checkpoint's ETA hour (Open-Meteo, batched + cached)   services/weather.py
   -> risk per checkpoint (wind / rain / snow + load rules)   services/risk.py
   -> miles per risk level, average risk, ranking              services/recommend.py
   -> 0-48 h heatmap frames along the corridor                 services/heatmap.py
```

Code map (`backend/routing/`):

| File | Responsibility |
|---|---|
| `views.py`, `serializers.py` | HTTP layer: validate input, map errors to 400 / 422 / 502 |
| `services/analyzer.py` | Orchestrates the steps above |
| `services/risk.py` | Threshold + load rules (pure functions) |
| `services/sampling.py` | Haversine distance, checkpoints, ETAs |
| `services/recommend.py` | Route stats and ranking (pure functions) |
| `services/geocoding.py`, `routing.py`, `weather.py` | Third-party clients |
| `services/heatmap.py` | Corridor grid and hourly intensity frames |

### Decisions worth knowing

- **Boundaries:** a reading exactly on a bound takes the higher level (wind 25 mph = Moderate). Rain > 1.00 and snow > 3.0 are No Travel; wind >= 55 is No Travel.
- **ETA:** constant average speed, so `ETA = departure + duration x fraction of route`. Weather is read for the hour of that ETA, not the departure hour.
- **Miles per level:** each checkpoint owns the stretch halfway to its neighbours.
- **Ranking:** No Travel miles, Severe miles, High miles, average risk (mile-weighted), then travel time. No Travel is ranked first because it is worse than Severe.
- **Checkpoint interval:** automatic (10 mi for trips up to 100 mi, 25 up to 300, else 50). Optionally send `checkpoint_interval_miles` as 10, 25 or 50.
- **Heatmap:** intensity = risk level / 4, using the same risk function and load rules. Frame `h` is `start_time + h` hours.
- **Scope:** worldwide place search by default (set `GEOCODING_COUNTRY=us` or `in,us` in `.env` to restrict it). Distances are in miles, wind in mph and load in lb, as the risk rules are defined in those units. No auth, no database.

## Setup (backend only)

Requires Python 3.11+.

```powershell
cd backend
python -m venv .venv
.venv\Scripts\activate            # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env            # macOS/Linux: cp .env.example .env
# edit .env and paste your MAPBOX_TOKEN
python manage.py runserver        # http://127.0.0.1:8000
```

### API keys

| Service | Used for | Key needed? |
|---|---|---|
| Mapbox | Geocoding + Directions (3 routes) | **Yes**, free |
| Open-Meteo | Hourly weather | No (free for non-commercial use) |

Get a Mapbox token: sign up at <https://account.mapbox.com/auth/signup/> (no credit card needed, free tier is 100,000 geocoding and 100,000 directions requests per month), then copy the **Default public token** (starts with `pk.`) from <https://account.mapbox.com/>. Put it in `backend/.env` as `MAPBOX_TOKEN`.

## API

### `POST /api/routes/analyze`

Request:

```json
{
  "origin": "Dallas, TX",
  "destination": "Denver, CO",
  "departure_time": "2026-10-19T08:00:00-05:00",
  "load_weight_lb": 42000,
  "checkpoint_interval_miles": null
}
```

`departure_time` must be within the next 10 days (not in the past). `load_weight_lb` is 0 to 80,000. `checkpoint_interval_miles` is optional: 10, 25 or 50.

Response (trimmed):

```json
{
  "recommended_route_id": "r2",
  "recommendation_reason": "Lowest Severe miles (0.0 vs 25.0, 40.0)",
  "routes": [{
    "id": "r2", "summary": "via I-287 N",
    "distance_miles": 781.2, "duration_hours": 12.4, "eta": "...",
    "geometry": [[32.78, -96.8], "..."],
    "stats": {
      "miles_by_risk": {"Low": 700.0, "Moderate": 51.2, "High": 30.0, "Severe": 0.0, "No Travel": 0.0},
      "no_travel_miles": 0.0, "severe_miles": 0.0, "high_miles": 30.0,
      "avg_risk": 0.21, "max_risk": "High", "no_travel": false
    },
    "checkpoints": [{
      "mile": 50.0, "lat": 33.1, "lng": -97.0, "eta": "...",
      "weather": {"wind_mph": 31.0, "rain_in_hr": 0.05, "snow_in_hr": 0.0},
      "risk": "Moderate", "risk_level": 1, "reason": "Wind 31 mph"
    }]
  }],
  "heatmap": {
    "start_time": "2026-10-19T13:00:00+00:00", "hours": 48,
    "points": [[32.8, -96.8], "..."],
    "frames": [[0.0, 0.25, "..."], "... 49 frames, one per hour"]
  },
  "origin": {"name": "...", "lat": 0, "lng": 0},
  "destination": {"name": "...", "lat": 0, "lng": 0},
  "warnings": []
}
```

Errors: `400` field validation (`{"origin": ["..."]}`), `422` unknown place or no route (`{"error": "..."}`), `502` Mapbox / Open-Meteo failure or missing token.

## Testing the backend

Automated (no API keys or network needed, external calls are mocked):

```powershell
cd backend
python -m pytest -q
```

Manual, with the server running (`python manage.py runserver`), using a departure time within the next 10 days:

```powershell
$body = @{
  origin = "Dallas, TX"; destination = "Denver, CO"
  departure_time = (Get-Date).AddHours(3).ToUniversalTime().ToString("o")
  load_weight_lb = 42000
} | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/api/routes/analyze `
  -ContentType "application/json" -Body $body | ConvertTo-Json -Depth 6
```

Or with curl (macOS/Linux/Git Bash):

```bash
curl -X POST http://127.0.0.1:8000/api/routes/analyze \
  -H "Content-Type: application/json" \
  -d '{"origin":"Dallas, TX","destination":"Denver, CO","departure_time":"2026-10-19T08:00:00-05:00","load_weight_lb":42000}'
```

Things to try: load 20,000 vs 45,000 in windy weather (the load rules change the risk), an empty `origin` (400), a nonsense place like `asdfqwer` (422), and no `MAPBOX_TOKEN` (502).
