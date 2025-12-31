"""Pydantic models for wedding seating optimization.

All models use strict mode (ConfigDict(strict=True)) to ensure
type coercion is disabled and inputs must match exact types.
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, StrictInt, StrictStr

# =============================================================================
# Request Models
# =============================================================================


class TableIn(BaseModel):
    """Input model for a circular table.

    Attributes:
        id: Unique identifier for the table.
        capacity: Number of seats (must be >= 2 for circular adjacency).
        label: Optional display label.
    """

    model_config = ConfigDict(strict=True)

    id: StrictStr
    capacity: StrictInt = Field(ge=2, description="Number of seats at the table")
    label: StrictStr | None = None


class GuestIn(BaseModel):
    """Input model for a wedding guest.

    Attributes:
        id: Unique identifier for the guest.
        name: Display name.
    """

    model_config = ConfigDict(strict=True)

    id: StrictStr
    name: StrictStr


class GroupIn(BaseModel):
    """A group of guests that must sit together at the same table.

    Attributes:
        id: Unique identifier for the group.
        guest_ids: List of guest IDs that must share a table.
    """

    model_config = ConfigDict(strict=True)

    id: StrictStr
    guest_ids: list[StrictStr] = Field(min_length=1)


class AffinityEdgeIn(BaseModel):
    """Affinity score between two groups.

    Affinity edges are unordered pairs. The solver maximizes total
    affinity for groups seated at the same table.

    Attributes:
        a: First group ID.
        b: Second group ID.
        score: Affinity score in {-1, 0, 1}.
            +1: Soft preference to be at same table.
            -1: Soft preference to NOT be at same table.
             0: No preference.
    """

    model_config = ConfigDict(strict=True)

    a: StrictStr
    b: StrictStr
    score: StrictInt = Field(ge=-1, le=1, description="Affinity score: -1, 0, or 1")


class SolveOptions(BaseModel):
    """Solver configuration options.

    Attributes:
        time_limit_seconds: Maximum solver runtime.
        num_workers: Number of parallel search workers.
        allow_empty_seats: Whether seats can remain unassigned.
    """

    model_config = ConfigDict(strict=True)

    time_limit_seconds: float = Field(default=5.0, gt=0)
    num_workers: StrictInt = Field(default=1, ge=1)
    allow_empty_seats: bool = True


class OptimizeRequest(BaseModel):
    """Request payload for seating optimization.

    Attributes:
        tables: List of tables with capacities.
        guests: List of guests to seat.
        groups: List of guest groups (guests in a group must sit together).
        affinities: Sparse list of affinity edges between groups (missing pairs score 0).
        options: Solver options.
    """

    model_config = ConfigDict(strict=True)

    tables: list[TableIn] = Field(min_length=1)
    guests: list[GuestIn] = Field(min_length=1)
    groups: list[GroupIn] = Field(default_factory=list)
    affinities: list[AffinityEdgeIn] = Field(default_factory=list)
    options: SolveOptions = Field(default_factory=SolveOptions)


# =============================================================================
# Response Models
# =============================================================================


class SeatAssignment(BaseModel):
    """Assignment of a guest to a specific seat.

    Attributes:
        seat_index: Position around the table (0-indexed).
        guest_id: Assigned guest ID, or None if empty.
        guest_name: Guest display name, or None if empty.
    """

    model_config = ConfigDict(strict=True)

    seat_index: StrictInt
    guest_id: StrictStr | None
    guest_name: StrictStr | None


class TableAssignment(BaseModel):
    """Complete seating assignment for a table.

    Attributes:
        table_id: Table identifier.
        seats: List of seat assignments (length = capacity).
    """

    model_config = ConfigDict(strict=True)

    table_id: StrictStr
    seats: list[SeatAssignment]


class SolverStats(BaseModel):
    """Statistics from the solver run.

    Attributes:
        conflicts: Number of conflicts encountered.
        branches: Number of search branches explored.
        wall_time_seconds: Total wall clock time.
    """

    model_config = ConfigDict(strict=True)

    conflicts: StrictInt
    branches: StrictInt
    wall_time_seconds: float


SolverStatus = Literal["OPTIMAL", "FEASIBLE", "INFEASIBLE", "UNKNOWN", "MODEL_INVALID"]


class OptimizeResponse(BaseModel):
    """Response from seating optimization.

    Attributes:
        status: Solver termination status.
        objective_value: Total affinity score achieved, if solution found.
        tables: Seating assignments per table.
        solver_stats: Performance statistics.
    """

    model_config = ConfigDict(strict=True)

    status: SolverStatus
    objective_value: StrictInt | None = None
    tables: list[TableAssignment] = Field(default_factory=list)
    solver_stats: SolverStats


class HealthResponse(BaseModel):
    """Health check response.

    Attributes:
        status: Service status ("ok").
        version: Service version.
    """

    model_config = ConfigDict(strict=True)

    status: Literal["ok"]
    version: StrictStr
