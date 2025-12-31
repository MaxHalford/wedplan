"""Router registration for the API."""

from fastapi import APIRouter

from wedplan.api.v1 import health, optimize

# Create v1 router
v1_router = APIRouter(prefix="/v1", tags=["v1"])
v1_router.include_router(optimize.router)

# Health is at root level (not versioned)
health_router = APIRouter(tags=["health"])
health_router.include_router(health.router)
