"""Main CP-SAT solver orchestration for wedding seating optimization.

This module provides the high-level solve_seating function that:
1. Validates and maps the input
2. Builds the CP-SAT model with all constraints
3. Solves and extracts the solution
"""

from ortools.sat.python.cp_model import CpModel, CpSolver, IntVar

from wedplan.domain.models import OptimizeRequest, OptimizeResponse
from wedplan.solver.constraints import (
    add_assignment_constraints,
    add_same_table_constraints,
    link_y_to_x,
)
from wedplan.solver.extract import extract_solution
from wedplan.solver.mapping import ProblemMapping, create_mapping
from wedplan.solver.objective import build_objective


def _create_decision_variables(
    model: CpModel, mapping: ProblemMapping
) -> tuple[dict[tuple[int, int, int], IntVar], dict[tuple[int, int], IntVar]]:
    """Create all decision variables for the model.

    Creates:
    - x[g, t, s]: guest g sits at table t seat s
    - y[g, t]: guest g sits at table t (any seat)

    Args:
        model: CP-SAT model.
        mapping: Problem mapping.

    Returns:
        Tuple of (x variables dict, y variables dict).
    """
    x: dict[tuple[int, int, int], IntVar] = {}
    y: dict[tuple[int, int], IntVar] = {}

    for g in range(mapping.num_guests):
        for t, table in enumerate(mapping.tables):
            # Table assignment variable
            y[g, t] = model.new_bool_var(f"y_{g}_{t}")

            # Seat assignment variables
            for s in range(table.capacity):
                x[g, t, s] = model.new_bool_var(f"x_{g}_{t}_{s}")

    return x, y


def solve_seating(request: OptimizeRequest) -> OptimizeResponse:
    """Solve the wedding seating optimization problem.

    This is the main entry point for the solver. It:
    1. Validates input and creates index mappings
    2. Builds the CP-SAT model with constraints
    3. Configures solver parameters
    4. Solves and returns the optimized seating

    Args:
        request: Optimization request with tables, guests, affinities,
                 constraints, and solver options.

    Returns:
        Optimization response with status, objective value, assignments,
        and solver statistics.

    Raises:
        GuestNotFoundError: If referenced guest ID not found.
        DuplicateIdError: If duplicate table or guest ID.
        DuplicateGroupMemberError: If guest appears twice in same group.
        GroupTooLargeError: If adjacent group exceeds max table capacity.
    """
    # Step 1: Create mapping (validates IDs and relationships)
    mapping = create_mapping(request)

    # Step 2: Create model and variables
    model = CpModel()
    x, y = _create_decision_variables(model, mapping)

    # Step 3: Add constraints

    # Basic assignment constraints
    add_assignment_constraints(model, x, mapping)

    # Link y to x (y[g,t] = OR of x[g,t,s])
    link_y_to_x(model, x, y, mapping)

    # Same-table group constraints (all guests in a group at same table)
    add_same_table_constraints(model, y, mapping)

    # Step 4: Build objective
    build_objective(
        model,
        y,
        request.affinities,
        mapping,
    )

    # Step 5: Configure and run solver
    solver = CpSolver()
    solver.parameters.max_time_in_seconds = request.options.time_limit_seconds
    solver.parameters.num_search_workers = request.options.num_workers

    status = solver.solve(model)

    # Step 6: Extract and return solution
    return extract_solution(solver, status, x, mapping)
