"""FastAPI Main Application: Incident Response Agent Backend."""
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import create_tables, engine
from app.routers import (
    incidents_router,
    agents_router,
    memory_router,
    postmortems_router,
    runbooks_router,
    simulation_router,
)
from app.services.hindsight_service import get_hindsight_service

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("incident-response-agent")
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize database tables
    logger.info("Initializing database tables...")
    create_tables()
    logger.info("Database initialized successfully.")
    yield
    # Shutdown
    logger.info("Shutting down Incident Response Agent backend.")


app = FastAPI(
    title="Hindsight-Powered Incident Response Agent",
    description="Autonomous incident response agent with long-term operational memory recall via Hindsight.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all for hackathon local dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(incidents_router)
app.include_router(agents_router)
app.include_router(memory_router)
app.include_router(postmortems_router)
app.include_router(runbooks_router)
app.include_router(simulation_router)


@app.get("/health", tags=["health"])
async def health_check():
    """System health check and integration status."""
    hs = get_hindsight_service()
    hs_health = await hs.health_check()

    return {
        "status": "healthy",
        "service": "Incident Response Agent",
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "database": "connected",
        "hindsight": {
            "connected": hs_health.get("connected", False),
            "bank_id": hs_health.get("bank_id"),
            "provider": hs_health.get("provider", "Hindsight"),
        },
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
