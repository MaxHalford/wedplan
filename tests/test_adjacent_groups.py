"""Test adjacent group constraints."""

import pytest

from wedplan.domain.errors import (
    DuplicateGroupMemberError,
    GroupTooLargeError,
    GuestNotFoundError,
)
from wedplan.domain.models import (
    AdjacentGroup,
    GuestIn,
    OptimizeRequest,
    SolveOptions,
    TableIn,
)
from wedplan.solver.cp_sat import solve_seating


def _are_contiguous(seats: list[int], capacity: int) -> bool:
    """Check if seat indices form a contiguous block around circular table."""
    if len(seats) <= 1:
        return True

    # Sort seats and check if they form a contiguous block
    # Need to handle wrap-around at circular table
    sorted_seats = sorted(seats)

    # Check normal contiguous (no wrap)
    normal_contiguous = all(
        sorted_seats[i + 1] - sorted_seats[i] == 1 for i in range(len(sorted_seats) - 1)
    )
    if normal_contiguous:
        return True

    # Check wrap-around contiguous
    # e.g., seats [0, 1, 5] with capacity 6 should be contiguous (5, 0, 1)
    gaps = []
    for i in range(len(sorted_seats) - 1):
        gaps.append(sorted_seats[i + 1] - sorted_seats[i])
    # Also check gap from last to first (wrap-around)
    wrap_gap = capacity - sorted_seats[-1] + sorted_seats[0]
    gaps.append(wrap_gap)

    # Exactly one gap should be > 1 (the "outside" gap)
    large_gaps = [g for g in gaps if g > 1]
    return len(large_gaps) <= 1


class TestAdjacentGroupContiguity:
    """Tests for adjacent group contiguous seating constraints."""

    def test_pair_is_contiguous(self) -> None:
        """A group of 2 must sit in adjacent seats."""
        request = OptimizeRequest(
            tables=[TableIn(id="t1", capacity=6)],
            guests=[
                GuestIn(id="alice", name="Alice"),
                GuestIn(id="bob", name="Bob"),
                GuestIn(id="carol", name="Carol"),
                GuestIn(id="dave", name="Dave"),
            ],
            adjacent_groups=[AdjacentGroup(guest_ids=["alice", "bob"])],
        )

        response = solve_seating(request)

        assert response.status in ("OPTIMAL", "FEASIBLE")

        # Find Alice and Bob's positions
        table = response.tables[0]
        alice_seat = None
        bob_seat = None
        for seat in table.seats:
            if seat.guest_id == "alice":
                alice_seat = seat.seat_index
            elif seat.guest_id == "bob":
                bob_seat = seat.seat_index

        assert alice_seat is not None
        assert bob_seat is not None

        # Check adjacency (circular)
        cap = len(table.seats)
        is_adjacent = (alice_seat + 1) % cap == bob_seat or (
            alice_seat - 1
        ) % cap == bob_seat
        assert is_adjacent, f"Alice at {alice_seat}, Bob at {bob_seat} not adjacent"

    def test_group_of_three_is_contiguous(self) -> None:
        """A group of 3 must sit in consecutive seats."""
        request = OptimizeRequest(
            tables=[TableIn(id="t1", capacity=8)],
            guests=[
                GuestIn(id="alice", name="Alice"),
                GuestIn(id="bob", name="Bob"),
                GuestIn(id="carol", name="Carol"),
                GuestIn(id="dave", name="Dave"),
                GuestIn(id="eve", name="Eve"),
            ],
            adjacent_groups=[AdjacentGroup(guest_ids=["alice", "bob", "carol"])],
        )

        response = solve_seating(request)

        assert response.status in ("OPTIMAL", "FEASIBLE")

        table = response.tables[0]
        group_seats = []
        for seat in table.seats:
            if seat.guest_id in ("alice", "bob", "carol"):
                group_seats.append(seat.seat_index)

        assert len(group_seats) == 3
        assert _are_contiguous(group_seats, len(table.seats)), (
            f"Group seats {group_seats} not contiguous"
        )

    def test_group_of_four_is_contiguous(self) -> None:
        """A group of 4 must sit in consecutive seats."""
        request = OptimizeRequest(
            tables=[TableIn(id="t1", capacity=6)],
            guests=[
                GuestIn(id="g1", name="G1"),
                GuestIn(id="g2", name="G2"),
                GuestIn(id="g3", name="G3"),
                GuestIn(id="g4", name="G4"),
                GuestIn(id="g5", name="G5"),
            ],
            adjacent_groups=[AdjacentGroup(guest_ids=["g1", "g2", "g3", "g4"])],
        )

        response = solve_seating(request)

        assert response.status in ("OPTIMAL", "FEASIBLE")

        table = response.tables[0]
        group_seats = []
        for seat in table.seats:
            if seat.guest_id in ("g1", "g2", "g3", "g4"):
                group_seats.append(seat.seat_index)

        assert len(group_seats) == 4
        assert _are_contiguous(group_seats, len(table.seats)), (
            f"Group seats {group_seats} not contiguous"
        )

    def test_multiple_groups(self) -> None:
        """Multiple groups each form contiguous blocks."""
        request = OptimizeRequest(
            tables=[TableIn(id="t1", capacity=10)],
            guests=[
                GuestIn(id="a1", name="A1"),
                GuestIn(id="a2", name="A2"),
                GuestIn(id="a3", name="A3"),
                GuestIn(id="b1", name="B1"),
                GuestIn(id="b2", name="B2"),
                GuestIn(id="c1", name="C1"),
            ],
            adjacent_groups=[
                AdjacentGroup(guest_ids=["a1", "a2", "a3"]),
                AdjacentGroup(guest_ids=["b1", "b2"]),
            ],
        )

        response = solve_seating(request)

        assert response.status in ("OPTIMAL", "FEASIBLE")

        table = response.tables[0]
        seats_by_guest: dict[str, int] = {}
        for seat in table.seats:
            if seat.guest_id:
                seats_by_guest[seat.guest_id] = seat.seat_index

        cap = len(table.seats)

        # Check A group contiguous
        a_seats = [seats_by_guest["a1"], seats_by_guest["a2"], seats_by_guest["a3"]]
        assert _are_contiguous(a_seats, cap), f"A group seats {a_seats} not contiguous"

        # Check B group contiguous
        b_seats = [seats_by_guest["b1"], seats_by_guest["b2"]]
        assert _are_contiguous(b_seats, cap), f"B group seats {b_seats} not contiguous"

    def test_groups_across_multiple_tables(self) -> None:
        """Groups stay together at same table with multiple tables available."""
        request = OptimizeRequest(
            tables=[
                TableIn(id="t1", capacity=4),
                TableIn(id="t2", capacity=4),
            ],
            guests=[
                GuestIn(id="a1", name="A1"),
                GuestIn(id="a2", name="A2"),
                GuestIn(id="a3", name="A3"),
                GuestIn(id="b1", name="B1"),
            ],
            adjacent_groups=[AdjacentGroup(guest_ids=["a1", "a2", "a3"])],
            options=SolveOptions(allow_empty_seats=True),
        )

        response = solve_seating(request)

        assert response.status in ("OPTIMAL", "FEASIBLE")

        # Find which table has the A group
        a_group_table = None
        a_seats = []
        for table in response.tables:
            table_a_seats = []
            for seat in table.seats:
                if seat.guest_id in ("a1", "a2", "a3"):
                    table_a_seats.append(seat.seat_index)
            if table_a_seats:
                a_group_table = table
                a_seats = table_a_seats

        assert a_group_table is not None
        assert len(a_seats) == 3, "All 3 group members must be at same table"
        cap = len(a_group_table.seats)
        assert _are_contiguous(a_seats, cap), f"A group seats {a_seats} not contiguous"


class TestAdjacentGroupValidation:
    """Tests for adjacent group validation errors."""

    def test_unknown_guest_rejected(self) -> None:
        """Unknown guest in group raises error."""
        request = OptimizeRequest(
            tables=[TableIn(id="t1", capacity=4)],
            guests=[
                GuestIn(id="alice", name="Alice"),
            ],
            adjacent_groups=[AdjacentGroup(guest_ids=["alice", "unknown"])],
        )

        with pytest.raises(GuestNotFoundError):
            solve_seating(request)

    def test_duplicate_guest_in_group_rejected(self) -> None:
        """Duplicate guest in same group raises error."""
        request = OptimizeRequest(
            tables=[TableIn(id="t1", capacity=4)],
            guests=[
                GuestIn(id="alice", name="Alice"),
                GuestIn(id="bob", name="Bob"),
            ],
            adjacent_groups=[AdjacentGroup(guest_ids=["alice", "alice", "bob"])],
        )

        with pytest.raises(DuplicateGroupMemberError):
            solve_seating(request)

    def test_group_too_large_rejected(self) -> None:
        """Group larger than any table capacity raises error."""
        request = OptimizeRequest(
            tables=[TableIn(id="t1", capacity=3)],
            guests=[
                GuestIn(id="g1", name="G1"),
                GuestIn(id="g2", name="G2"),
                GuestIn(id="g3", name="G3"),
                GuestIn(id="g4", name="G4"),
            ],
            adjacent_groups=[AdjacentGroup(guest_ids=["g1", "g2", "g3", "g4"])],
        )

        with pytest.raises(GroupTooLargeError):
            solve_seating(request)
