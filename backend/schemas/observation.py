from pydantic import BaseModel
from typing import Optional

class ObservationOut(BaseModel):
    component_id: str
    anomaly_score: Optional[float] = None
    defect_type: Optional[str] = None
    defect_confidence: Optional[float] = None
    severity: Optional[float] = None
    risk: Optional[float] = None
    risk_level: Optional[str] = None
    bbox: Optional[list] = None
    heatmap_path: Optional[str] = None
    contributors: Optional[dict] = None

class ComponentOut(BaseModel):
    component_id: str
    component_type: str
    line_id: Optional[str] = None
    track_id: Optional[str] = None
    chainage_m: Optional[float] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    criticality: Optional[float] = None
