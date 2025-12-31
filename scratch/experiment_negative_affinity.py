"""Burner script to test negative affinity scoring concept.

Tests that:
1. Negative affinity (-1) penalizes same-table placement
2. Positive affinity (+1) rewards same-table placement
3. The simplified objective function works correctly

Run with:
    source ./venv/bin/activate && ./venv/bin/python scratch/experiment_negative_affinity.py
"""

from ortools.sat.python.cp_model import FEASIBLE, OPTIMAL, CpModel, CpSolver, IntVar


def create_colocated_var(
    model: CpModel,
    y: dict[tuple[int, int], IntVar],
    i: int,
    j: int,
    num_tables: int,
) -> IntVar:
    """Create variable indicating if guests i and j are at same table."""
    colocated = model.new_bool_var(f"colocated_{i}_{j}")

    same_table_t: list[IntVar] = []
    for t in range(num_tables):
        st = model.new_bool_var(f"same_table_{i}_{j}_{t}")
        model.add_implication(st, y[i, t])
        model.add_implication(st, y[j, t])
        model.add_bool_or([y[i, t].Not(), y[j, t].Not(), st])
        same_table_t.append(st)

    model.add_max_equality(colocated, same_table_t)
    return colocated


def test_negative_affinity_penalizes_same_table() -> None:
    """Test that negative affinity score penalizes same-table placement.

    Setup:
    - 2 tables with 2 seats each
    - 2 guests: Alice and Bob
    - Affinity(Alice, Bob) = -1 (they should NOT be at same table)

    Expected: Solver places them at different tables.
    """
    print("\n" + "=" * 60)
    print("TEST: Negative affinity (-1) penalizes same-table placement")
    print("=" * 60)

    model = CpModel()

    num_guests = 2
    num_tables = 2
    capacity = 2

    # Decision variables
    # x[g, t, s] = guest g at table t seat s
    x: dict[tuple[int, int, int], any] = {}
    # y[g, t] = guest g at table t
    y: dict[tuple[int, int], any] = {}

    for g in range(num_guests):
        for t in range(num_tables):
            y[g, t] = model.new_bool_var(f"y_{g}_{t}")
            for s in range(capacity):
                x[g, t, s] = model.new_bool_var(f"x_{g}_{t}_{s}")

    # Constraint: each guest exactly one seat
    for g in range(num_guests):
        model.add_exactly_one(x[g, t, s] for t in range(num_tables) for s in range(capacity))

    # Constraint: each seat at most one guest
    for t in range(num_tables):
        for s in range(capacity):
            model.add_at_most_one(x[g, t, s] for g in range(num_guests))

    # Link y to x
    for g in range(num_guests):
        for t in range(num_tables):
            seats = [x[g, t, s] for s in range(capacity)]
            model.add_max_equality(y[g, t], seats)

    # Create colocated variable
    colocated = create_colocated_var(model, y, 0, 1, num_tables)

    # Objective: score * colocated
    # With score = -1, this becomes: -1 * colocated
    # Maximizing this means minimizing colocated (prefer NOT same table)
    score = -1
    model.maximize(score * colocated)

    # Solve
    solver = CpSolver()
    status = solver.solve(model)

    print(f"Status: {status} (OPTIMAL={OPTIMAL}, FEASIBLE={FEASIBLE})")
    print(f"Objective: {solver.objective_value}")
    print(f"Colocated: {solver.value(colocated)}")

    # Check placement
    for g in range(num_guests):
        for t in range(num_tables):
            if solver.value(y[g, t]):
                print(f"Guest {g} -> Table {t}")

    # Verify: with negative affinity, they should be at DIFFERENT tables
    are_colocated = solver.value(colocated) == 1
    print(f"\nResult: Guests are {'SAME' if are_colocated else 'DIFFERENT'} table")
    assert not are_colocated, "FAIL: Guests should be at different tables with negative affinity!"
    print("PASS: Negative affinity correctly separated guests!")


def test_positive_affinity_rewards_same_table() -> None:
    """Test that positive affinity score rewards same-table placement.

    Setup:
    - 2 tables with 2 seats each
    - 2 guests: Alice and Bob
    - Affinity(Alice, Bob) = +1 (they SHOULD be at same table)

    Expected: Solver places them at the same table.
    """
    print("\n" + "=" * 60)
    print("TEST: Positive affinity (+1) rewards same-table placement")
    print("=" * 60)

    model = CpModel()

    num_guests = 2
    num_tables = 2
    capacity = 2

    x: dict[tuple[int, int, int], any] = {}
    y: dict[tuple[int, int], any] = {}

    for g in range(num_guests):
        for t in range(num_tables):
            y[g, t] = model.new_bool_var(f"y_{g}_{t}")
            for s in range(capacity):
                x[g, t, s] = model.new_bool_var(f"x_{g}_{t}_{s}")

    for g in range(num_guests):
        model.add_exactly_one(x[g, t, s] for t in range(num_tables) for s in range(capacity))

    for t in range(num_tables):
        for s in range(capacity):
            model.add_at_most_one(x[g, t, s] for g in range(num_guests))

    for g in range(num_guests):
        for t in range(num_tables):
            seats = [x[g, t, s] for s in range(capacity)]
            model.add_max_equality(y[g, t], seats)

    colocated = create_colocated_var(model, y, 0, 1, num_tables)

    # Objective: +1 * colocated = reward same table
    score = 1
    model.maximize(score * colocated)

    solver = CpSolver()
    status = solver.solve(model)

    print(f"Status: {status} (OPTIMAL={OPTIMAL}, FEASIBLE={FEASIBLE})")
    print(f"Objective: {solver.objective_value}")
    print(f"Colocated: {solver.value(colocated)}")

    for g in range(num_guests):
        for t in range(num_tables):
            if solver.value(y[g, t]):
                print(f"Guest {g} -> Table {t}")

    are_colocated = solver.value(colocated) == 1
    print(f"\nResult: Guests are {'SAME' if are_colocated else 'DIFFERENT'} table")
    assert are_colocated, "FAIL: Guests should be at same table with positive affinity!"
    print("PASS: Positive affinity correctly grouped guests!")


def test_mixed_affinities() -> None:
    """Test mixed positive and negative affinities.

    Setup:
    - 2 tables with 3 seats each
    - 4 guests: A, B, C, D
    - Affinity(A, B) = +1 (should be together)
    - Affinity(A, C) = -1 (should be apart)
    - Affinity(C, D) = +1 (should be together)

    Expected: A+B at one table, C+D at another table.
    """
    print("\n" + "=" * 60)
    print("TEST: Mixed positive and negative affinities")
    print("=" * 60)

    model = CpModel()

    num_guests = 4
    num_tables = 2
    capacity = 3

    x: dict[tuple[int, int, int], any] = {}
    y: dict[tuple[int, int], any] = {}

    for g in range(num_guests):
        for t in range(num_tables):
            y[g, t] = model.new_bool_var(f"y_{g}_{t}")
            for s in range(capacity):
                x[g, t, s] = model.new_bool_var(f"x_{g}_{t}_{s}")

    for g in range(num_guests):
        model.add_exactly_one(x[g, t, s] for t in range(num_tables) for s in range(capacity))

    for t in range(num_tables):
        for s in range(capacity):
            model.add_at_most_one(x[g, t, s] for g in range(num_guests))

    for g in range(num_guests):
        for t in range(num_tables):
            seats = [x[g, t, s] for s in range(capacity)]
            model.add_max_equality(y[g, t], seats)

    # Create colocated variables
    colocated_ab = create_colocated_var(model, y, 0, 1, num_tables)  # A=0, B=1
    colocated_ac = create_colocated_var(model, y, 0, 2, num_tables)  # A=0, C=2
    colocated_cd = create_colocated_var(model, y, 2, 3, num_tables)  # C=2, D=3

    # Objective: sum of score * colocated
    # A-B: +1, A-C: -1, C-D: +1
    objective = (
        1 * colocated_ab  # reward A+B together
        + -1 * colocated_ac  # penalize A+C together
        + 1 * colocated_cd  # reward C+D together
    )
    model.maximize(objective)

    solver = CpSolver()
    status = solver.solve(model)

    print(f"Status: {status}")
    print(f"Objective: {solver.objective_value}")
    print(f"Colocated A-B: {solver.value(colocated_ab)}")
    print(f"Colocated A-C: {solver.value(colocated_ac)}")
    print(f"Colocated C-D: {solver.value(colocated_cd)}")

    guest_names = ["A", "B", "C", "D"]
    for g in range(num_guests):
        for t in range(num_tables):
            if solver.value(y[g, t]):
                print(f"Guest {guest_names[g]} -> Table {t}")

    # Verify
    ab_together = solver.value(colocated_ab) == 1
    ac_apart = solver.value(colocated_ac) == 0
    cd_together = solver.value(colocated_cd) == 1

    print(f"\nA-B together: {ab_together} (expected: True)")
    print(f"A-C apart: {ac_apart} (expected: True)")
    print(f"C-D together: {cd_together} (expected: True)")

    # Optimal objective should be: +1 (A-B) + 0 (A-C apart) + 1 (C-D) = 2
    assert solver.objective_value == 2, f"Expected objective 2, got {solver.objective_value}"
    assert ab_together, "FAIL: A and B should be together"
    assert ac_apart, "FAIL: A and C should be apart"
    assert cd_together, "FAIL: C and D should be together"
    print("PASS: Mixed affinities handled correctly!")


def test_zero_affinity_no_preference() -> None:
    """Test that zero affinity has no effect on placement."""
    print("\n" + "=" * 60)
    print("TEST: Zero affinity (0) has no preference")
    print("=" * 60)

    model = CpModel()

    num_guests = 2
    num_tables = 2
    capacity = 2

    x: dict[tuple[int, int, int], any] = {}
    y: dict[tuple[int, int], any] = {}

    for g in range(num_guests):
        for t in range(num_tables):
            y[g, t] = model.new_bool_var(f"y_{g}_{t}")
            for s in range(capacity):
                x[g, t, s] = model.new_bool_var(f"x_{g}_{t}_{s}")

    for g in range(num_guests):
        model.add_exactly_one(x[g, t, s] for t in range(num_tables) for s in range(capacity))

    for t in range(num_tables):
        for s in range(capacity):
            model.add_at_most_one(x[g, t, s] for g in range(num_guests))

    for g in range(num_guests):
        for t in range(num_tables):
            seats = [x[g, t, s] for s in range(capacity)]
            model.add_max_equality(y[g, t], seats)

    colocated = create_colocated_var(model, y, 0, 1, num_tables)

    # Objective: 0 * colocated = 0 (no preference)
    score = 0
    model.maximize(score * colocated)

    solver = CpSolver()
    status = solver.solve(model)

    print(f"Status: {status}")
    print(f"Objective: {solver.objective_value}")
    print(f"Colocated: {solver.value(colocated)}")

    for g in range(num_guests):
        for t in range(num_tables):
            if solver.value(y[g, t]):
                print(f"Guest {g} -> Table {t}")

    # With zero affinity, objective should be 0 regardless of placement
    assert solver.objective_value == 0, f"Expected objective 0, got {solver.objective_value}"
    print("PASS: Zero affinity has no effect on objective!")


if __name__ == "__main__":
    print("=" * 60)
    print("EXPERIMENT: Testing Negative Affinity Scoring Concept")
    print("=" * 60)

    test_negative_affinity_penalizes_same_table()
    test_positive_affinity_rewards_same_table()
    test_mixed_affinities()
    test_zero_affinity_no_preference()

    print("\n" + "=" * 60)
    print("ALL TESTS PASSED!")
    print("=" * 60)
    print("\nConclusion: The simplified objective function works correctly:")
    print("  - score * colocated handles both positive and negative affinities")
    print("  - Negative score (-1) penalizes same-table placement")
    print("  - Positive score (+1) rewards same-table placement")
    print("  - Zero score (0) has no effect")
