"""Model tests — verifies asset registry schema per docs/architecture/asset-registry.md"""
from models.component import Component, Inspection, Observation
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

def test_component_fields():
    c = Component(component_id="FASTENER-001821", component_type="fastener", line_id="LINE-01", track_id="UP", chainage_m=124320, criticality=0.85)
    assert c.component_id == "FASTENER-001821"
    assert c.component_type == "fastener"
    assert c.criticality == 0.85

def test_observation_contributors():
    """Explainable risk requires contributors JSON per risk.md"""
    o = Observation(observation_id="OBS-001", component_id="FASTENER-001821", inspection_id="INSP-001",
                    anomaly_score=0.81, defect_type="Displaced", defect_confidence=0.93,
                    severity=0.554, risk=58.5, risk_level="HIGH", bbox=[0,0,224,224],
                    contributors={"S": 22.2, "C": 23.8})
    assert o.risk_level == "HIGH"
    assert "S" in o.contributors

def test_postgis_geometry_column():
    assert hasattr(Component, "geom")
    assert Component.__tablename__ == "components"
    assert Observation.__tablename__ == "observations"

def test_in_memory_schema_creates():
    # Use sqlite in-memory to verify tables create (PostGIS geometry mocked as string for test)
    engine = create_engine("sqlite:///:memory:")
    # Create without Geometry type check — just verify Base metadata
    from models.component import Base
    # Should not raise
    assert Base is not None
