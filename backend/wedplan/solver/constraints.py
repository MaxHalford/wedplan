"""Constraint builders for the CP-SAT model.

Implements:
- Adjacent group constraints (must sit in contiguous seats at same table)
- Same-table group constraints
"""

from ortools.sat.python.cp_model import CpModel, IntVar

from wedplan.domain.errors import GuestNotFoundError
from wedplan.domain.models import SameTableConstraintIn
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
        model.add_exactly_one(
            x[g, t, s]
            for t, table in enumerate(mapping.tables)
            for s in range(table.capacity)
        )

    # Each seat at most one guest
    for t, table in enumerate(mapping.tables):
        for s in range(table.capacity):
            model.add_at_most_one(x[g, t, s] for g in range(mapping.num_guests))


def add_adjacent_group_constraints(
    model: CpModel,
    x: dict[tuple[int, int, int], IntVar],
    y: dict[tuple[int, int], IntVar],
    mapping: ProblemMapping,
) -> None:
    """Add contiguous seating constraints for adjacent groups.

    All members of a group must sit at the same table in consecutive seats.
    Order within the group is flexible (any permutation allowed).

    For a group of N guests, they occupy a contiguous block of N seats.
    The block wraps around circularly.

    Args:
        model: CP-SAT model.
        x: Decision variables x[g, t, s].
        y: Table assignment variables y[g, t].
        mapping: Problem mapping.
    """
    for group_idx, group in enumerate(mapping.adjacent_groups):
        n = len(group)

        # Collect all possible block assignments (table, start_seat)
        block_vars: list[IntVar] = []

        for t, table in enumerate(mapping.tables):
            cap = table.capacity

            # Skip tables that can't fit the group
            if n > cap:
                continue

            for start in range(cap):
                # Block seats: start, start+1, ..., start+n-1 (mod cap)
                block_seats = [(start + i) % cap for i in range(n)]

                # Create variable: "group occupies this block"
                block_var = model.new_bool_var(
                    f"group_{group_idx}_table_{t}_start_{start}"
                )
                block_vars.append(block_var)

                # If block_var is true, all group members are in block_seats
                # and each block seat has exactly one group member
                for g in group:
                    # g must be in one of the block seats
                    in_block = [x[g, t, s] for s in block_seats]
                    # block_var => OR(in_block)
                    model.add_bool_or([block_var.Not(), *in_block])

                # Each block seat has exactly one group member (if block active)
                for s in block_seats:
                    guests_at_seat = [x[g, t, s] for g in group]
                    # If block_var, exactly one group member at seat s
                    # sum(guests_at_seat) >= 1 when block_var
                    at_least_one = model.add(sum(guests_at_seat) >= 1)
                    at_least_one.only_enforce_if(block_var)
                    # sum <= 1 is already ensured by assignment constraints

        # Exactly one block is chosen for this group
        if block_vars:
            model.add_exactly_one(block_vars)

        # Also enforce same-table constraint for group members
        if len(group) >= 2:
            first = group[0]
            for other in group[1:]:
                for t in range(mapping.num_tables):
                    model.add(y[first, t] == y[other, t])


def add_same_table_constraints(
    model: CpModel,
    y: dict[tuple[int, int], IntVar],
    same_table: SameTableConstraintIn | None,
    mapping: ProblemMapping,
) -> None:
    """Add same-table group constraints.

    All guests in a group must sit at the same table.
    Implemented by enforcing y[i, t] == y[j, t] for all pairs in group.

    Args:
        model: CP-SAT model.
        y: Table assignment variables y[g, t].
        same_table: Same-table constraint specification.
        mapping: Problem mapping.

    Raises:
        GuestNotFoundError: If referenced guest ID not found.
    """
    if same_table is None:
        return

    for group in same_table.groups:
        # Validate all guest IDs exist
        indices: list[int] = []
        for guest_id in group.guest_ids:
            if guest_id not in mapping.guest_id_to_index:
                raise GuestNotFoundError(guest_id, "same_table constraint")
            indices.append(mapping.guest_id_to_index[guest_id])

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
