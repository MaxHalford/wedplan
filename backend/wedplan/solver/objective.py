"""Objective function builder for affinity scoring.

Maximizes total affinity between groups seated at the same table.
Positive affinity (+1) rewards same-table placement.
Negative affinity (-1) penalizes same-table placement.
"""

from ortools.sat.python.cp_model import CpModel, IntVar, LinearExpr

from wedplan.domain.errors import GroupNotFoundError
from wedplan.domain.models import AffinityEdgeIn
from wedplan.solver.mapping import ProblemMapping


def _create_groups_colocated_var(
    model: CpModel,
    y: dict[tuple[int, int], IntVar],
    group1_rep_guest: int,
    group2_rep_guest: int,
    group1_id: str,
    group2_id: str,
    num_tables: int,
) -> IntVar:
    """Create variable indicating if two groups are at the same table.

    Since all guests in a group are constrained to sit at the same table,
    we only need to check if a representative guest from each group
    is at the same table.

    colocated = 1 iff there exists table t where y[rep1,t] = y[rep2,t] = 1.

    Args:
        model: CP-SAT model.
        y: Table assignment variables.
        group1_rep_guest: Representative guest index from group 1.
        group2_rep_guest: Representative guest index from group 2.
        group1_id: Group 1 ID (for naming).
        group2_id: Group 2 ID (for naming).
        num_tables: Number of tables.

    Returns:
        Boolean variable indicating group co-location.
    """
    colocated = model.new_bool_var(f"groups_colocated_{group1_id}_{group2_id}")

    # same_table_t[t] = y[rep1,t] AND y[rep2,t]
    same_table_t: list[IntVar] = []
    for t in range(num_tables):
        st = model.new_bool_var(f"groups_same_table_{group1_id}_{group2_id}_{t}")

        # st => y[rep1,t] AND st => y[rep2,t]
        model.add_implication(st, y[group1_rep_guest, t])
        model.add_implication(st, y[group2_rep_guest, t])

        # y[rep1,t] AND y[rep2,t] => st
        model.add_bool_or([y[group1_rep_guest, t].Not(), y[group2_rep_guest, t].Not(), st])

        same_table_t.append(st)

    # colocated = OR(same_table_t)
    model.add_max_equality(colocated, same_table_t)

    return colocated


def build_objective(
    model: CpModel,
    y: dict[tuple[int, int], IntVar],
    affinities: list[AffinityEdgeIn],
    mapping: ProblemMapping,
) -> dict[tuple[int, int], IntVar]:
    """Build the objective function for group affinity maximization.

    Objective = sum(score * groups_colocated[G1, G2])

    For positive scores (+1), this rewards same-table placement of groups.
    For negative scores (-1), this penalizes same-table placement of groups.

    Args:
        model: CP-SAT model.
        y: Table assignment variables.
        affinities: List of affinity edges between groups.
        mapping: Problem mapping.

    Returns:
        Dictionary of groups_colocated variables.

    Raises:
        GroupNotFoundError: If affinity references unknown group.
    """
    colocated_vars: dict[tuple[int, int], IntVar] = {}
    objective_terms: list[LinearExpr | int] = []

    for edge in affinities:
        # Validate group IDs
        if edge.a not in mapping.group_id_to_index:
            raise GroupNotFoundError(edge.a, "affinity edge")
        if edge.b not in mapping.group_id_to_index:
            raise GroupNotFoundError(edge.b, "affinity edge")

        group1_idx = mapping.group_id_to_index[edge.a]
        group2_idx = mapping.group_id_to_index[edge.b]

        # Canonical ordering
        key = (min(group1_idx, group2_idx), max(group1_idx, group2_idx))

        # Create colocated variable if not exists
        if key not in colocated_vars:
            group1 = mapping.groups[key[0]]
            group2 = mapping.groups[key[1]]

            # Use first guest of each group as representative
            # (all guests in a group are at the same table due to constraints)
            rep1 = group1.guest_indices[0]
            rep2 = group2.guest_indices[0]

            colocated_vars[key] = _create_groups_colocated_var(
                model, y, rep1, rep2, group1.id, group2.id, mapping.num_tables
            )

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
