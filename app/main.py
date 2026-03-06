import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .db import engine, Base
from .api.routes import reviews, scores, segments, safe_points,ai

app = FastAPI(title="Safescape Backend")

# CORS (website + dev)
origins = os.getenv("CORS_ORIGINS")
allow_origins = ["*"] if not origins else [o.strip() for o in origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    # MVP: auto-create tables
    Base.metadata.create_all(bind=engine)

@app.get("/health")
def health():
    return {"ok": True}

# Routers
app.include_router(reviews.router)
app.include_router(scores.router)
app.include_router(segments.router)
app.include_router(safe_points.router)