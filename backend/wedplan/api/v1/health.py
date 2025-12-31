"""Health check endpoint."""

from fastapi import APIRouter

from wedplan import __version__
from wedplan.domain.models import HealthResponse

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Returns service status and version.",
)
def health() -> HealthResponse:
    """Health check endpoint.

    Returns:
        Health response with status and version.
    """
    return HealthResponse(status="ok", version=__version__)
