"""Objective function builder for affinity scoring.

Maximizes total affinity between guests seated at the same table,
with optional adjacency bonus for guests in adjacent seats.
"""

from ortools.sat.python.cp_model import CpModel, IntVar, LinearExpr

from wedplan.domain.errors import GuestNotFoundError
from wedplan.domain.models import AffinityEdgeIn
from wedplan.solver.mapping import ProblemMapping


def _create_colocated_var(
    model: CpModel,
    y: dict[tuple[int, int], IntVar],
    i: int,
    j: int,
    num_tables: int,
) -> IntVar:
    """Create variable indicating if guests i and j are at same table.

    colocated[i,j] = 1 iff there exists table t where y[i,t] = y[j,t] = 1.

    Since each guest is at exactly one table, this is equivalent to:
    colocated = OR_t(y[i,t] AND y[j,t])

    Implemented using auxiliary variables for each table.

    Args:
        model: CP-SAT model.
        y: Table assignment variables.
        i: First guest index.
        j: Second guest index.
        num_tables: Number of tables.

    Returns:
        Boolean variable indicating co-location.
    """
    colocated = model.new_bool_var(f"colocated_{i}_{j}")

    # same_table_t[t] = y[i,t] AND y[j,t]
    same_table_t: list[IntVar] = []
    for t in range(num_tables):
        st = model.new_bool_var(f"same_table_{i}_{j}_{t}")

        # st => y[i,t] AND st => y[j,t]
        model.add_implication(st, y[i, t])
        model.add_implication(st, y[j, t])

        # y[i,t] AND y[j,t] => st
        # Equivalent to: NOT y[i,t] OR NOT y[j,t] OR st
        model.add_bool_or([y[i, t].Not(), y[j, t].Not(), st])

        same_table_t.append(st)

    # colocated = OR(same_table_t)
    # colocated => at least one same_table_t
    # If colocated = 1, then at least one same_table_t = 1
    model.add_max_equality(colocated, same_table_t)

    return colocated


def _create_adjacent_var(
    model: CpModel,
    x: dict[tuple[int, int, int], IntVar],
    i: int,
    j: int,
    mapping: ProblemMapping,
) -> IntVar:
    """Create variable indicating if guests i and j are in adjacent seats.

    adjacent = 1 iff guests are at same table in neighboring seats.

    Args:
        model: CP-SAT model.
        x: Seat assignment variables.
        i: First guest index.
        j: Second guest index.
        mapping: Problem mapping.

    Returns:
        Boolean variable indicating adjacency.
    """
    adjacent = model.new_bool_var(f"adjacent_{i}_{j}")

    # Collect all adjacent seat pairs across tables
    adjacent_pairs: list[IntVar] = []

    for t, table in enumerate(mapping.tables):
        cap = table.capacity
        for s in range(cap):
            # Check if i at seat s and j at neighbor
            right = (s + 1) % cap

            # pair_var = x[i,t,s] AND x[j,t,right]
            pair_var = model.new_bool_var(f"adj_pair_{i}_{j}_{t}_{s}")

            model.add_implication(pair_var, x[i, t, s])
            model.add_implication(pair_var, x[j, t, right])
            model.add_bool_or(
                [
                    x[i, t, s].Not(),
                    x[j, t, right].Not(),
                    pair_var,
                ]
            )

            adjacent_pairs.append(pair_var)

            # Also check symmetric: j at seat s and i at right
            pair_var2 = model.new_bool_var(f"adj_pair_{j}_{i}_{t}_{s}")

            model.add_implication(pair_var2, x[j, t, s])
            model.add_implication(pair_var2, x[i, t, right])
            model.add_bool_or(
                [
                    x[j, t, s].Not(),
                    x[i, t, right].Not(),
                    pair_var2,
                ]
            )

            adjacent_pairs.append(pair_var2)

    # adjacent = OR(all adjacent pairs)
    if adjacent_pairs:
        model.add_max_equality(adjacent, adjacent_pairs)
    else:
        # No seats, adjacent is always false
        model.add(adjacent == 0)

    return adjacent


def build_objective(
    model: CpModel,
    x: dict[tuple[int, int, int], IntVar],
    y: dict[tuple[int, int], IntVar],
    affinities: list[AffinityEdgeIn],
    mapping: ProblemMapping,
    adjacency_bonus_weight: int,
) -> tuple[dict[tuple[int, int], IntVar], dict[tuple[int, int], IntVar]]:
    """Build the objective function for affinity maximization.

    Objective = sum(score * colocated[i,j]) + weight * sum(adj_bonus * adjacent[i,j])

    Args:
        model: CP-SAT model.
        x: Seat assignment variables.
        y: Table assignment variables.
        affinities: List of affinity edges.
        mapping: Problem mapping.
        adjacency_bonus_weight: Multiplier for adjacency bonus.

    Returns:
        Tuple of (colocated variables dict, adjacent variables dict).

    Raises:
        GuestNotFoundError: If affinity references unknown guest.
    """
    colocated_vars: dict[tuple[int, int], IntVar] = {}
    adjacent_vars: dict[tuple[int, int], IntVar] = {}

    objective_terms: list[LinearExpr | int] = []

    for edge in affinities:
        # Validate guest IDs
        if edge.a not in mapping.guest_id_to_index:
            raise GuestNotFoundError(edge.a, "affinity edge")
        if edge.b not in mapping.guest_id_to_index:
            raise GuestNotFoundError(edge.b, "affinity edge")

        i = mapping.guest_id_to_index[edge.a]
        j = mapping.guest_id_to_index[edge.b]

        # Canonical ordering
        key = (min(i, j), max(i, j))

        # Create colocated variable if not exists
        if key not in colocated_vars:
            colocated_vars[key] = _create_colocated_var(
                model, y, key[0], key[1], mapping.num_tables
            )

        # Add same-table affinity to objective
        if edge.score > 0:
            objective_terms.append(edge.score * colocated_vars[key])

        # Handle adjacency bonus
        if edge.adjacency_bonus is not None and edge.adjacency_bonus > 0:
            if key not in adjacent_vars:
                adjacent_vars[key] = _create_adjacent_var(
                    model, x, key[0], key[1], mapping
                )

            bonus = adjacency_bonus_weight * edge.adjacency_bonus
            objective_terms.append(bonus * adjacent_vars[key])

    # Set objective
    if objective_terms:
        model.maximize(sum(objective_terms))
    else:
        # No affinities, just find any feasible solution
        model.maximize(0)

    return colocated_vars, adjacent_vars
