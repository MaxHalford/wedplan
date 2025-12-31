"""Seating optimization endpoint."""

from fastapi import APIRouter, HTTPException

from wedplan.domain.errors import ValidationError, WedplanError
from wedplan.domain.models import OptimizeRequest, OptimizeResponse
from wedplan.solver.cp_sat import solve_seating

router = APIRouter()


@router.post(
    "/optimize",
    response_model=OptimizeResponse,
    summary="Optimize wedding seating",
    description=(
        "Finds optimal seating arrangement that maximizes affinity scores "
        "while respecting partner adjacency and same-table constraints."
    ),
    responses={
        422: {
            "description": "Validation error (invalid guest/table references, "
            "asymmetric partners, etc.)"
        },
    },
)
def optimize(request: OptimizeRequest) -> OptimizeResponse:
    """Optimize wedding seating arrangement.

    Args:
        request: Optimization request with tables, guests, affinities,
                 and constraints.

    Returns:
        Optimization response with seating assignments.

    Raises:
        HTTPException: 422 for domain validation errors.
    """
    try:
        return solve_seating(request)
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=e.message) from e
    except WedplanError as e:
        raise HTTPException(status_code=500, detail=e.message) from e
