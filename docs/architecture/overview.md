# Architecture Overview

## 1. End-to-End Flow

```mermaid
flowchart TD
    A["Railway Image / Video<br/>Inspection source"] --> B["Frame Preprocessing<br/>resize / normalize / deblur"]
    B --> C["Component Detection<br/>YOLO / RT-DETR<br/>Rail / Fastener / Sleeper / Fishplate"]
    C --> D1["Known Defect Detector<br/>Supervised: YOLO heads<br/>RFDD, Surface Faults"]
    C --> D2["RailSense Anomaly Engine<br/>ResNet50 encoder + decoder<br/>MSE + top-k + SSIM"]
    D1 --> E["Evidence Fusion<br/>known_conf + anomaly + localization"]
    D2 --> E
    E --> F["Defect Localization<br/>bbox + anomaly heatmap"]
    F --> G["Condition Assessment<br/>Ct = [At,Dt,St,Lt,Qt]"]
    G --> H["Severity Engine<br/>S = w1D+w2A+w3G+w4C"]
    H --> I["Asset Identification<br/>GPS / Chainage / Track / Line"]
    I --> J["Asset Database<br/>lines → tracks → components → inspections"]
    J --> K{"Repeated inspections<br/>for same asset?"}
    K -->|No| L["Risk Engine v1<br/>R = w1S+w2C+w3A+w4L"]
    K -->|Yes| M["Temporal Engine v2<br/>Association + Deterioration"]
    M --> N["Risk Engine v2<br/>R = w1S+w2D+w3C+w4A+w5L"]
    L --> O["Dashboard<br/>Map + Detail + Queue"]
    N --> O
```

## 2. Five Layers (Simplified)

```mermaid
flowchart TD
    L1["Layer 1: Component Detection<br/>YOLO / Segmentation"] --> L2["Layer 2: Anomaly Detection<br/>RailSense Autoencoder"]
    L2 --> L3["Layer 3: Severity<br/>Anomaly + Area + Criticality"]
    L3 --> L4["Layer 4: Temporal<br/>Same Asset → Deterioration"]
    L4 --> L5["Layer 5: Prioritization<br/>Risk → Queue"]
```

## 3. Component View

```mermaid
graph TB
    subgraph ML["ML Layer"]
        CD["component_detection<br/>train.py / inference.py / configs/"]
        DD["defect_detection<br/>RFDD fastener head<br/>Surface rail head"]
        AD["anomaly_detection<br/>railsense / patchcore / padim<br/>model.py / scoring.py / train.py"]
        SEV["severity<br/>severity_engine.py"]
        TEMP["temporal<br/>association.py / deterioration.py"]
        RISK["risk<br/>risk_engine.py"]
    end
    subgraph BE["Backend"]
        API["FastAPI / api/"]
        SVC["services/"]
        DB[("PostgreSQL + PostGIS<br/>SQLAlchemy models")]
    end
    subgraph FE["Frontend"]
        REACT["React + Vite + Tailwind"]
        MAP["Leaflet / MapLibre"]
        CHART["Recharts"]
    end
    CD --> AD
    CD --> DD
    AD --> SEV
    DD --> SEV
    SEV --> TEMP
    TEMP --> RISK
    RISK --> SVC
    SVC --> API
    SVC --> DB
    API --> REACT
    REACT --> MAP
    REACT --> CHART
```

## 4. Data Flow — Single Component Example

```mermaid
sequenceDiagram
    participant Cam as Camera / Video
    participant Det as Component Detector
    participant Crop as Crop
    participant Ano as RailSense
    participant Fus as Fusion
    participant Sev as Severity
    participant DB as Asset DB
    participant Risk as Risk Engine
    participant UI as Dashboard

    Cam->>Det: full frame (e.g., 1920x1080)
    Det->>Crop: bbox {fastener, 0.97}
    Crop->>Ano: 128x128 crop
    Ano->>Fus: {anomaly: 0.71, heatmap, SSIM}
    Det->>Fus: {known_defect: displaced, conf: 0.93}
    Fus->>Sev: {A=0.71, D=displaced, L=heatmap, Q=0.93}
    Sev->>DB: Ct + S=68
    DB->>Risk: history [0.51, 0.62, 0.74, 0.71]
    Risk->>UI: {risk: 86, level: CRITICAL, contributors}
```

## 5. Why Detector Before Anomaly

Real inspection frames are full scenes with multiple components at varying scales. RailSense was trained on component crops in a controlled proxy environment. Without detection → cropping, full frames would be fed to a crop-trained autoencoder, destroying performance.

```mermaid
flowchart LR
    F["Full Frame<br/>rail + sleepers + 2 fasteners"] --> DET["Component Detector"]
    DET --> C1["Crop: Fastener 1"]
    DET --> C2["Crop: Fastener 2"]
    DET --> C3["Crop: Rail segment"]
    C1 --> RS["RailSense<br/>fastener model"]
    C2 --> RS
    C3 --> RS2["RailSense<br/>rail model"]
```

This also enables **component-specific anomaly models** (H2: component-specific > generic).

## 6. Asset-Centric vs Image-Centric

```mermaid
erDiagram
    LINES ||--o{ TRACKS : contains
    TRACKS ||--o{ COMPONENTS : contains
    COMPONENTS ||--o{ INSPECTIONS : observed_in
    INSPECTIONS ||--o{ OBSERVATIONS : has
    OBSERVATIONS ||--o{ ANOMALIES : yields
    OBSERVATIONS ||--o{ SEVERITY : scored_as
    COMPONENTS ||--o{ RISK : prioritized_by

    COMPONENTS {
        string component_id PK
        string type
        string line
        string track
        float chainage_m
        float lat
        float lon
        float criticality
    }
    OBSERVATIONS {
        string observation_id PK
        string component_id FK
        string inspection_id
        datetime timestamp
        float anomaly_score
        string defect_type
        float severity
        json bbox
        string heatmap_path
    }
```

## 7. Deployment Topology (Conceptual)

```mermaid
flowchart TD
    Edge["Edge: Inspection Vehicle<br/>Camera + GPS + Jetson<br/>YOLO inference"] --> Ingest["Ingest Service<br/>Frame extraction + upload"]
    Ingest --> Backend["Backend<br/>FastAPI<br/>Component crop → RailSense → Severity → Risk"]
    Backend --> DB[("PostgreSQL + PostGIS + Redis")]
    Backend --> FE["Frontend<br/>Map + Queue + Detail"]
    Backend --> WB["W&B<br/>Experiment tracking"]
```

## 8. Key Design Constraints

- **No temporal inference without asset association** — temporal path is gated.
- **Prototype weights** — severity/risk weights are experimental, not safety thresholds; must be documented as such.
- **Heatmap ≠ segmentation** until validated against RFDD pixel masks.
- **PostGIS required for spatial queries** — chainage + GPS + track ID together, not GPS alone.
