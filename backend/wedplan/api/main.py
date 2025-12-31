"""FastAPI application factory."""

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

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

    # Add CORS middleware for frontend dev server and production
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.get_cors_origins(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include API routers first (they take precedence)
    app.include_router(health_router)
    app.include_router(v1_router)

    # Serve static files if the dist directory exists (production)
    static_path = Path(settings.static_dir)
    if static_path.exists() and static_path.is_dir():
        # Mount static assets (js, css, etc.)
        app.mount("/assets", StaticFiles(directory=static_path / "assets"), name="assets")

        # SPA fallback: serve index.html for non-API routes
        @app.get("/{full_path:path}")
        async def serve_spa(request: Request, full_path: str) -> FileResponse:
            """Serve the SPA index.html for client-side routing.

            Args:
                request: The incoming request.
                full_path: The requested path.

            Returns:
                The index.html file for SPA routing.
            """
            index_file = static_path / "index.html"
            if index_file.exists():
                return FileResponse(index_file)
            return FileResponse(static_path / "index.html")

    return app


# Application instance for uvicorn/FastAPI CLI
app = create_app()
