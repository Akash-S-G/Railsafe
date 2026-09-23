# Backend — FastAPI + PostGIS

## Run (local)

```bash
cp backend/.env.example backend/.env  # edit if needed
docker compose up -d db
cd backend && pip install -r requirements.txt
uvicorn api.main:app --reload
# open http://localhost:8000/docs
```

## Structure

```
backend/
  api/main.py            # FastAPI app + CORS + /health
  api/routers_assets.py  # stub — Phase 8/9 PostGIS queries
  models/component.py    # SQLAlchemy + GeoAlchemy2 (Point 4326)
  schemas/observation.py # Pydantic
  requirements.txt
  Dockerfile
```

## DB

PostGIS `postgis/postgis:15-3.4` via `docker-compose.yml`. Tables: `components`, `inspections`, `observations` (with `contributors` JSON for explainability).
