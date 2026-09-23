# Asset Registry & Spatial Representation

## 1. Central Entity: `component_id`

```text
FASTENER-001821
RAIL-004102
SLEEPER-000913
FISHPLATE-000442
```

All observations attach to this ID. Image-level results are ephemeral; asset-level records are persistent.

## 2. Schema

```mermaid
erDiagram
    RAILWAY_LINES ||--o{ TRACKS : has
    TRACKS ||--o{ COMPONENTS : contains
    COMPONENTS ||--o{ INSPECTIONS : via_observations
    INSPECTIONS ||--o{ OBSERVATIONS : includes
    OBSERVATIONS ||--o{ ANOMALIES : produces
    OBSERVATIONS ||--o{ SEVERITY : scored
    COMPONENTS ||--o{ RISK : ranked

    RAILWAY_LINES {
        string line_id PK
        string name
    }
    TRACKS {
        string track_id PK
        string line_id FK
        string direction
    }
    COMPONENTS {
        string component_id PK
        string type
        string track_id FK
        float chainage_m
        float lat
        float lon
        float criticality
    }
    INSPECTIONS {
        string inspection_id PK
        datetime timestamp
        string vehicle_id
    }
    OBSERVATIONS {
        string observation_id PK
        string component_id FK
        string inspection_id FK
        float anomaly_score
        string defect_type
        float severity
        json bbox
        string heatmap_path
    }
```

## 3. Spatial Representation

GPS alone is insufficient for railway asset management. Use triple:

```json
{
  "line": "LINE-01",
  "track": "UP",
  "chainage_m": 124320,
  "latitude": 12.123456,
  "longitude": 77.123456
}
```

- `chainage` = linear distance along track (authoritative for ordering).
- `GPS` = geographic position for mapping.
- `track` + `line` = disambiguation.

Database: **PostgreSQL + PostGIS** for spatial indexing and `chainage` range queries.

```mermaid
flowchart TD
    A["Observation<br/>bbox + GPS + chainage"] --> B["Spatial Index<br/>PostGIS"]
    B --> C["Map Query<br/>bbox or chainage range"]
    C --> D["Components in view"]
    D --> E["Risk-colored pins"]
```

## 4. Asset Identification at Ingest

```mermaid
flowchart TD
    F["New detection<br/>bbox + GPS + chainage"] --> Q["Query nearby assets<br/>chainage ± Δ + track"]
    Q --> M{"Match found?"}
    M -->|Yes| U["Update asset<br/>new observation"]
    M -->|No| C["Create asset<br/>new component_id"]
```

Phase 1 (v1): simple spatial assignment (chainage window). Phase 2: full temporal association (see `temporal.md`).

## 5. API Sketch

```text
GET  /assets?line=LINE-01&chainage_from=124000&chainage_to=125000
GET  /assets/{component_id}
GET  /assets/{component_id}/history
POST /inspections  (upload frames + GPS/chainage)
```

See `backend/` scaffold.
