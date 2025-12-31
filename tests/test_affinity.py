"""Test affinity scoring behavior between groups."""

from wedplan.domain.models import (
    AffinityEdgeIn,
    GroupIn,
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

    def test_negative_affinity_separates_groups(self) -> None:
        """Groups with negative affinity should be at different tables."""
        request = OptimizeRequest(
            tables=[
                TableIn(id="t1", capacity=2),
                TableIn(id="t2", capacity=2),
            ],
            guests=[
                GuestIn(id="alice", name="Alice"),
                GuestIn(id="bob", name="Bob"),
            ],
            groups=[
                GroupIn(id="g_alice", guest_ids=["alice"]),
                GroupIn(id="g_bob", guest_ids=["bob"]),
            ],
            affinities=[
                AffinityEdgeIn(a="g_alice", b="g_bob", score=-1),
            ],
        )

        response = solve_seating(request)

        assert response.status in ("OPTIMAL", "FEASIBLE")

        alice_table = _get_guest_table(response, "alice")
        bob_table = _get_guest_table(response, "bob")

        assert alice_table is not None
        assert bob_table is not None
        assert alice_table != bob_table, (
            f"Alice and Bob groups should be at different tables with negative affinity, but both are at {alice_table}"
        )

    def test_negative_affinity_with_multiple_groups(self) -> None:
        """Negative affinity works with more groups."""
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
            groups=[
                GroupIn(id="g_alice", guest_ids=["alice"]),
                GroupIn(id="g_bob", guest_ids=["bob"]),
                GroupIn(id="g_carol", guest_ids=["carol"]),
                GroupIn(id="g_dave", guest_ids=["dave"]),
            ],
            affinities=[
                AffinityEdgeIn(a="g_alice", b="g_bob", score=-1),  # Keep apart
            ],
        )

        response = solve_seating(request)

        assert response.status in ("OPTIMAL", "FEASIBLE")

        alice_table = _get_guest_table(response, "alice")
        bob_table = _get_guest_table(response, "bob")

        assert alice_table != bob_table, "Negative affinity should keep Alice and Bob groups apart"


class TestPositiveAffinity:
    """Tests for positive affinity behavior (rewards same-table)."""

    def test_positive_affinity_groups_together(self) -> None:
        """Groups with positive affinity should be at the same table."""
        request = OptimizeRequest(
            tables=[
                TableIn(id="t1", capacity=2),
                TableIn(id="t2", capacity=2),
            ],
            guests=[
                GuestIn(id="alice", name="Alice"),
                GuestIn(id="bob", name="Bob"),
            ],
            groups=[
                GroupIn(id="g_alice", guest_ids=["alice"]),
                GroupIn(id="g_bob", guest_ids=["bob"]),
            ],
            affinities=[
                AffinityEdgeIn(a="g_alice", b="g_bob", score=1),
            ],
        )

        response = solve_seating(request)

        assert response.status in ("OPTIMAL", "FEASIBLE")

        alice_table = _get_guest_table(response, "alice")
        bob_table = _get_guest_table(response, "bob")

        assert alice_table is not None
        assert bob_table is not None
        assert alice_table == bob_table, (
            f"Alice and Bob groups should be at the same table with positive affinity, "
            f"but Alice is at {alice_table} and Bob is at {bob_table}"
        )


class TestMixedAffinity:
    """Tests for mixed positive and negative affinities."""

    def test_mixed_affinities(self) -> None:
        """Mixed affinities should be handled correctly.

        Setup:
        - Group Alice-Bob: +1 affinity with themselves (same table)
        - Group Carol-Dave: +1 affinity with themselves (same table)
        - Group Alice-Bob and Carol-Dave: -1 affinity (different tables)

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
            groups=[
                # Alice and Bob in same group
                GroupIn(id="g_ab", guest_ids=["alice", "bob"]),
                # Carol and Dave in same group
                GroupIn(id="g_cd", guest_ids=["carol", "dave"]),
            ],
            affinities=[
                # These two groups should be apart
                AffinityEdgeIn(a="g_ab", b="g_cd", score=-1),
            ],
        )

        response = solve_seating(request)

        assert response.status in ("OPTIMAL", "FEASIBLE")

        alice_table = _get_guest_table(response, "alice")
        bob_table = _get_guest_table(response, "bob")
        carol_table = _get_guest_table(response, "carol")
        dave_table = _get_guest_table(response, "dave")

        # Alice and Bob are in the same group, so same table
        assert alice_table == bob_table, "Alice and Bob should be together (same group)"
        # Carol and Dave are in the same group, so same table
        assert carol_table == dave_table, "Carol and Dave should be together (same group)"
        # The two groups should be at different tables
        assert alice_table != carol_table, "Group AB and Group CD should be apart"


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
            groups=[
                GroupIn(id="g_alice", guest_ids=["alice"]),
                GroupIn(id="g_bob", guest_ids=["bob"]),
            ],
            affinities=[
                AffinityEdgeIn(a="g_alice", b="g_bob", score=0),
            ],
        )

        response = solve_seating(request)

        assert response.status in ("OPTIMAL", "FEASIBLE")
        # Objective should be 0 since score=0 contributes nothing
        assert response.objective_value == 0


class TestMultiMemberGroups:
    """Tests for groups with multiple members."""

    def test_group_members_stay_together(self) -> None:
        """All members of a group should be at the same table."""
        request = OptimizeRequest(
            tables=[
                TableIn(id="t1", capacity=4),
                TableIn(id="t2", capacity=4),
            ],
            guests=[
                GuestIn(id="alice", name="Alice"),
                GuestIn(id="bob", name="Bob"),
                GuestIn(id="carol", name="Carol"),
                GuestIn(id="dave", name="Dave"),
            ],
            groups=[
                GroupIn(id="family", guest_ids=["alice", "bob", "carol"]),
                GroupIn(id="single", guest_ids=["dave"]),
            ],
        )

        response = solve_seating(request)

        assert response.status in ("OPTIMAL", "FEASIBLE")

        alice_table = _get_guest_table(response, "alice")
        bob_table = _get_guest_table(response, "bob")
        carol_table = _get_guest_table(response, "carol")

        assert alice_table == bob_table == carol_table, "All family members should be at the same table"

    def test_positive_affinity_between_multi_member_groups(self) -> None:
        """Positive affinity between multi-member groups seats them together."""
        request = OptimizeRequest(
            tables=[
                TableIn(id="t1", capacity=6),
                TableIn(id="t2", capacity=6),
            ],
            guests=[
                GuestIn(id="a1", name="A1"),
                GuestIn(id="a2", name="A2"),
                GuestIn(id="b1", name="B1"),
                GuestIn(id="b2", name="B2"),
            ],
            groups=[
                GroupIn(id="team_a", guest_ids=["a1", "a2"]),
                GroupIn(id="team_b", guest_ids=["b1", "b2"]),
            ],
            affinities=[
                AffinityEdgeIn(a="team_a", b="team_b", score=1),
            ],
        )

        response = solve_seating(request)

        assert response.status in ("OPTIMAL", "FEASIBLE")

        a1_table = _get_guest_table(response, "a1")
        b1_table = _get_guest_table(response, "b1")

        assert a1_table == b1_table, "Team A and Team B should be at the same table with positive affinity"
