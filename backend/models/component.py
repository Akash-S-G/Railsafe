"""PostGIS-enabled asset registry — v1, no temporal history yet."""
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import declarative_base, relationship
from geoalchemy2 import Geometry
import datetime

Base = declarative_base()

class Component(Base):
    __tablename__ = "components"
    component_id = Column(String, primary_key=True)  # e.g., FASTENER-001821
    component_type = Column(String, nullable=False)  # rail/fastener/sleeper/fishplate
    line_id = Column(String, nullable=True)
    track_id = Column(String, nullable=True)
    chainage_m = Column(Float, nullable=True)
    lat = Column(Float, nullable=True)
    lon = Column(Float, nullable=True)
    criticality = Column(Float, nullable=True)  # engineering prior, not CV
    geom = Column(Geometry("POINT", srid=4326), nullable=True)  # PostGIS
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Inspection(Base):
    __tablename__ = "inspections"
    inspection_id = Column(String, primary_key=True)
    timestamp = Column(DateTime, nullable=False)
    vehicle_id = Column(String, nullable=True)

class Observation(Base):
    __tablename__ = "observations"
    observation_id = Column(String, primary_key=True)
    component_id = Column(String, ForeignKey("components.component_id"), nullable=False)
    inspection_id = Column(String, ForeignKey("inspections.inspection_id"), nullable=False)
    anomaly_score = Column(Float, nullable=True)
    defect_type = Column(String, nullable=True)  # per-dataset head label or null
    defect_confidence = Column(Float, nullable=True)
    severity = Column(Float, nullable=True)
    risk = Column(Float, nullable=True)
    risk_level = Column(String, nullable=True)  # LOW/MEDIUM/HIGH/CRITICAL
    bbox = Column(JSON, nullable=True)  # [x,y,w,h]
    heatmap_path = Column(String, nullable=True)
    contributors = Column(JSON, nullable=True)  # explainability breakdown
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    component = relationship("Component")
    inspection = relationship("Inspection")
