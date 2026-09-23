from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="RailSafe API", version="0.1.0 - v1 (no temporal)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "ok", "version": "v1", "temporal": "gated"}

@app.get("/")
def root():
    return {"name": "RailSafe", "docs": "/docs", "health": "/health"}

# Routers will be included here in Phase 8-9
# from .routers import assets, inspections, detections
# app.include_router(assets.router, prefix="/assets")
