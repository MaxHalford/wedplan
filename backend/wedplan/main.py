"""FastAPI application entry point."""

from fastapi import FastAPI

app = FastAPI(
    title="WedPlan",
    description="Wedding seating optimization service",
    version="0.1.0",
)


@app.get("/health")
def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}
