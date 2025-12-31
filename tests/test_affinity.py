"""Test affinity scoring behavior."""

from wedplan.domain.models import (
    AffinityEdgeIn,
    GuestIn,
    OptimizeRequest,
    TableIn,
)
from wedplan.solver.cp_sat import solve_seating


def _get_guest_table(response, guest_id: str) -> str | None:
    """Get the table ID where a guest is seated."""
    for table in response.tables:
        for seat in table.seats:
            if seat.guest_id == guest_id:
                return table.table_id
    return None


class TestNegativeAffinity:
    """Tests for negative affinity behavior (penalizes same-table)."""

    def test_negative_affinity_separates_guests(self) -> None:
        """Guests with negative affinity should be at different tables."""
        request = OptimizeRequest(
            tables=[
                TableIn(id="t1", capacity=2),
                TableIn(id="t2", capacity=2),
            ],
            guests=[
                GuestIn(id="alice", name="Alice"),
                GuestIn(id="bob", name="Bob"),
            ],
            affinities=[
                AffinityEdgeIn(a="alice", b="bob", score=-1),
            ],
        )

        response = solve_seating(request)

        assert response.status in ("OPTIMAL", "FEASIBLE")

        alice_table = _get_guest_table(response, "alice")
        bob_table = _get_guest_table(response, "bob")

        assert alice_table is not None
        assert bob_table is not None
        assert alice_table != bob_table, (
            f"Alice and Bob should be at different tables with negative affinity, but both are at {alice_table}"
        )

    def test_negative_affinity_with_multiple_guests(self) -> None:
        """Negative affinity works with more guests."""
        request = OptimizeRequest(
            tables=[
                TableIn(id="t1", capacity=3),
                TableIn(id="t2", capacity=3),
            ],
            guests=[
                GuestIn(id="alice", name="Alice"),
                GuestIn(id="bob", name="Bob"),
                GuestIn(id="carol", name="Carol"),
                GuestIn(id="dave", name="Dave"),
            ],
            affinities=[
                AffinityEdgeIn(a="alice", b="bob", score=-1),  # Keep apart
            ],
        )

        response = solve_seating(request)

        assert response.status in ("OPTIMAL", "FEASIBLE")

        alice_table = _get_guest_table(response, "alice")
        bob_table = _get_guest_table(response, "bob")

        assert alice_table != bob_table, "Negative affinity should keep Alice and Bob apart"


class TestPositiveAffinity:
    """Tests for positive affinity behavior (rewards same-table)."""

    def test_positive_affinity_groups_guests(self) -> None:
        """Guests with positive affinity should be at the same table."""
        request = OptimizeRequest(
            tables=[
                TableIn(id="t1", capacity=2),
                TableIn(id="t2", capacity=2),
            ],
            guests=[
                GuestIn(id="alice", name="Alice"),
                GuestIn(id="bob", name="Bob"),
            ],
            affinities=[
                AffinityEdgeIn(a="alice", b="bob", score=1),
            ],
        )

        response = solve_seating(request)

        assert response.status in ("OPTIMAL", "FEASIBLE")

        alice_table = _get_guest_table(response, "alice")
        bob_table = _get_guest_table(response, "bob")

        assert alice_table is not None
        assert bob_table is not None
        assert alice_table == bob_table, (
            f"Alice and Bob should be at the same table with positive affinity, "
            f"but Alice is at {alice_table} and Bob is at {bob_table}"
        )


class TestMixedAffinity:
    """Tests for mixed positive and negative affinities."""

    def test_mixed_affinities(self) -> None:
        """Mixed affinities should be handled correctly.

        Setup:
        - Alice and Bob: +1 (should be together)
        - Alice and Carol: -1 (should be apart)
        - Carol and Dave: +1 (should be together)

        Expected: Alice+Bob at one table, Carol+Dave at another.
        """
        request = OptimizeRequest(
            tables=[
                TableIn(id="t1", capacity=3),
                TableIn(id="t2", capacity=3),
            ],
            guests=[
                GuestIn(id="alice", name="Alice"),
                GuestIn(id="bob", name="Bob"),
                GuestIn(id="carol", name="Carol"),
                GuestIn(id="dave", name="Dave"),
            ],
            affinities=[
                AffinityEdgeIn(a="alice", b="bob", score=1),  # Together
                AffinityEdgeIn(a="alice", b="carol", score=-1),  # Apart
                AffinityEdgeIn(a="carol", b="dave", score=1),  # Together
            ],
        )

        response = solve_seating(request)

        assert response.status in ("OPTIMAL", "FEASIBLE")

        alice_table = _get_guest_table(response, "alice")
        bob_table = _get_guest_table(response, "bob")
        carol_table = _get_guest_table(response, "carol")
        dave_table = _get_guest_table(response, "dave")

        # Optimal objective = 2 (alice-bob together + carol-dave together, alice-carol apart)
        assert response.objective_value == 2

        assert alice_table == bob_table, "Alice and Bob should be together"
        assert carol_table == dave_table, "Carol and Dave should be together"
        assert alice_table != carol_table, "Alice and Carol should be apart"


class TestZeroAffinity:
    """Tests for zero affinity (no preference)."""

    def test_zero_affinity_no_effect(self) -> None:
        """Zero affinity should not affect objective."""
        request = OptimizeRequest(
            tables=[
                TableIn(id="t1", capacity=2),
                TableIn(id="t2", capacity=2),
            ],
            guests=[
                GuestIn(id="alice", name="Alice"),
                GuestIn(id="bob", name="Bob"),
            ],
            affinities=[
                AffinityEdgeIn(a="alice", b="bob", score=0),
            ],
        )

        response = solve_seating(request)

        assert response.status in ("OPTIMAL", "FEASIBLE")
        # Objective should be 0 since score=0 contributes nothing
        assert response.objective_value == 0
