"""Solution extraction from CP-SAT solver to response DTO."""

from ortools.sat.python.cp_model import CpSolver, IntVar

from wedplan.domain.models import (
    OptimizeResponse,
    SeatAssignment,
    SolverStats,
    SolverStatus,
    TableAssignment,
)
from wedplan.solver.mapping import ProblemMapping


def _status_to_string(status: int) -> SolverStatus:
    """Convert OR-Tools status code to string.

    Args:
        status: OR-Tools CpSolverStatus enum value.

    Returns:
        Status string literal.
    """
    # OR-Tools status codes
    # UNKNOWN = 0, MODEL_INVALID = 1, FEASIBLE = 2, INFEASIBLE = 3, OPTIMAL = 4
    status_map: dict[int, SolverStatus] = {
        0: "UNKNOWN",
        1: "MODEL_INVALID",
        2: "FEASIBLE",
        3: "INFEASIBLE",
        4: "OPTIMAL",
    }
    return status_map.get(status, "UNKNOWN")


def extract_solution(
    solver: CpSolver,
    status: int,
    x: dict[tuple[int, int, int], IntVar],
    mapping: ProblemMapping,
) -> OptimizeResponse:
    """Extract solution from solver into response DTO.

    Args:
        solver: Solved CP-SAT solver.
        status: Solver status code.
        x: Seat assignment decision variables.
        mapping: Problem mapping.

    Returns:
        Complete optimization response.
    """
    status_str = _status_to_string(status)

    # Build solver stats
    stats = SolverStats(
        conflicts=int(solver.num_conflicts),
        branches=int(solver.num_branches),
        wall_time_seconds=solver.wall_time,
    )

    # No solution found
    if status_str not in ("OPTIMAL", "FEASIBLE"):
        return OptimizeResponse(
            status=status_str,
            objective_value=None,
            tables=[],
            solver_stats=stats,
        )

    # Extract assignments
    table_assignments: list[TableAssignment] = []

    for t, table in enumerate(mapping.tables):
        seats: list[SeatAssignment] = []

        for s in range(table.capacity):
            # Find which guest (if any) is at this seat
            assigned_guest_idx: int | None = None
            for g in range(mapping.num_guests):
                if solver.boolean_value(x[g, t, s]):
                    assigned_guest_idx = g
                    break

            if assigned_guest_idx is not None:
                guest = mapping.guests[assigned_guest_idx]
                seats.append(
                    SeatAssignment(
                        seat_index=s,
                        guest_id=guest.id,
                        guest_name=guest.name,
                    )
                )
            else:
                seats.append(
                    SeatAssignment(
                        seat_index=s,
                        guest_id=None,
                        guest_name=None,
                    )
                )

        table_assignments.append(
            TableAssignment(
                table_id=table.id,
                seats=seats,
            )
        )

    return OptimizeResponse(
        status=status_str,
        objective_value=int(solver.objective_value),
        tables=table_assignments,
        solver_stats=stats,
    )
