"""Objective function builder for affinity scoring.

Maximizes total affinity between guests seated at the same table.
Positive affinity (+1) rewards same-table placement.
Negative affinity (-1) penalizes same-table placement.
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


def build_objective(
    model: CpModel,
    y: dict[tuple[int, int], IntVar],
    affinities: list[AffinityEdgeIn],
    mapping: ProblemMapping,
) -> dict[tuple[int, int], IntVar]:
    """Build the objective function for affinity maximization.

    Objective = sum(score * colocated[i,j])

    For positive scores (+1), this rewards same-table placement.
    For negative scores (-1), this penalizes same-table placement.

    Args:
        model: CP-SAT model.
        y: Table assignment variables.
        affinities: List of affinity edges.
        mapping: Problem mapping.

    Returns:
        Dictionary of colocated variables.

    Raises:
        GuestNotFoundError: If affinity references unknown guest.
    """
    colocated_vars: dict[tuple[int, int], IntVar] = {}
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
            colocated_vars[key] = _create_colocated_var(model, y, key[0], key[1], mapping.num_tables)

        # Add affinity term to objective
        # score * colocated works for both positive and negative:
        # +1 * colocated = reward same table
        # -1 * colocated = penalize same table
        if edge.score != 0:
            objective_terms.append(edge.score * colocated_vars[key])

    # Set objective
    if objective_terms:
        model.maximize(sum(objective_terms))
    else:
        # No affinities, just find any feasible solution
        model.maximize(0)

    return colocated_vars
