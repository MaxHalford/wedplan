"""FastAPI application factory."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from wedplan import __version__
from wedplan.api.routes import health_router, v1_router
from wedplan.core.config import get_settings


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        Configured FastAPI application instance.
    """
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        description="Wedding seating optimization service using OR-Tools CP-SAT",
        version=__version__,
        debug=settings.debug,
    )

    # Add CORS middleware for frontend dev server
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(health_router)
    app.include_router(v1_router)

    return app


# Application instance for uvicorn/FastAPI CLI
app = create_app()
