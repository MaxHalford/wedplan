"""Constraint builders for the CP-SAT model.

Implements:
- Basic assignment constraints (each guest to exactly one seat)
- Same-table group constraints (guests in a group must sit together)
"""

from ortools.sat.python.cp_model import CpModel, IntVar

from wedplan.solver.mapping import ProblemMapping


def add_assignment_constraints(
    model: CpModel,
    x: dict[tuple[int, int, int], IntVar],
    mapping: ProblemMapping,
) -> None:
    """Add basic assignment constraints.

    - Each guest is assigned to exactly one seat.
    - Each seat has at most one guest.

    Args:
        model: CP-SAT model.
        x: Decision variables x[g, t, s].
        mapping: Problem mapping.
    """
    # Each guest exactly one seat
    for g in range(mapping.num_guests):
        model.add_exactly_one(x[g, t, s] for t, table in enumerate(mapping.tables) for s in range(table.capacity))

    # Each seat at most one guest
    for t, table in enumerate(mapping.tables):
        for s in range(table.capacity):
            model.add_at_most_one(x[g, t, s] for g in range(mapping.num_guests))


def add_same_table_constraints(
    model: CpModel,
    y: dict[tuple[int, int], IntVar],
    mapping: ProblemMapping,
) -> None:
    """Add same-table group constraints.

    All guests in a group must sit at the same table.
    Implemented by enforcing y[i, t] == y[j, t] for all pairs in group.

    Args:
        model: CP-SAT model.
        y: Table assignment variables y[g, t].
        mapping: Problem mapping (groups already validated during mapping creation).
    """
    for group in mapping.groups:
        # Group guest indices are already validated during mapping creation
        indices = group.guest_indices

        # Enforce pairwise equality for table assignment
        # If i and j must be at same table, then y[i,t] == y[j,t] for all t
        if len(indices) < 2:
            continue

        first = indices[0]
        for other in indices[1:]:
            for t in range(mapping.num_tables):
                # y[first, t] == y[other, t]
                # This is a boolean equality constraint
                model.add(y[first, t] == y[other, t])


def link_y_to_x(
    model: CpModel,
    x: dict[tuple[int, int, int], IntVar],
    y: dict[tuple[int, int], IntVar],
    mapping: ProblemMapping,
) -> None:
    """Link table assignment variables y to seat assignment variables x.

    y[g, t] = 1 iff guest g is at any seat of table t.
    Implemented as: y[g, t] == OR(x[g, t, s] for all s)

    Since each guest is assigned exactly one seat, at most one y[g, t] is 1.

    Args:
        model: CP-SAT model.
        x: Seat assignment variables x[g, t, s].
        y: Table assignment variables y[g, t].
        mapping: Problem mapping.
    """
    for g in range(mapping.num_guests):
        for t, table in enumerate(mapping.tables):
            seats_at_table = [x[g, t, s] for s in range(table.capacity)]

            # y[g, t] == 1 iff any x[g, t, s] == 1
            # Using add_max_equality: y = max(seats) which is OR for booleans
            model.add_max_equality(y[g, t], seats_at_table)
