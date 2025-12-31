"""Test partner adjacency constraints."""

import pytest

from wedplan.domain.errors import AsymmetricPartnerError, PartnerCycleError
from wedplan.domain.models import (
    GuestIn,
    OptimizeRequest,
    SolveOptions,
    TableIn,
)
from wedplan.solver.cp_sat import solve_seating


class TestPartnerAdjacency:
    """Tests for partner adjacency constraints."""

    def test_partners_are_adjacent(self) -> None:
        """Partners must be seated in adjacent seats."""
        request = OptimizeRequest(
            tables=[TableIn(id="t1", capacity=6)],
            guests=[
                GuestIn(id="alice", name="Alice", partner_id="bob"),
                GuestIn(id="bob", name="Bob", partner_id="alice"),
                GuestIn(id="carol", name="Carol"),
                GuestIn(id="dave", name="Dave"),
            ],
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

    def test_multiple_partner_pairs(self) -> None:
        """Multiple partner pairs are all adjacent."""
        request = OptimizeRequest(
            tables=[TableIn(id="t1", capacity=8)],
            guests=[
                GuestIn(id="a1", name="A1", partner_id="a2"),
                GuestIn(id="a2", name="A2", partner_id="a1"),
                GuestIn(id="b1", name="B1", partner_id="b2"),
                GuestIn(id="b2", name="B2", partner_id="b1"),
                GuestIn(id="c1", name="C1"),
                GuestIn(id="c2", name="C2"),
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

        # Check A pair
        a1_seat = seats_by_guest["a1"]
        a2_seat = seats_by_guest["a2"]
        assert (a1_seat + 1) % cap == a2_seat or (a1_seat - 1) % cap == a2_seat, (
            f"A pair not adjacent: {a1_seat}, {a2_seat}"
        )

        # Check B pair
        b1_seat = seats_by_guest["b1"]
        b2_seat = seats_by_guest["b2"]
        assert (b1_seat + 1) % cap == b2_seat or (b1_seat - 1) % cap == b2_seat, (
            f"B pair not adjacent: {b1_seat}, {b2_seat}"
        )

    def test_partners_across_multiple_tables(self) -> None:
        """Partners at same table and adjacent even with multiple tables."""
        request = OptimizeRequest(
            tables=[
                TableIn(id="t1", capacity=4),
                TableIn(id="t2", capacity=4),
            ],
            guests=[
                GuestIn(id="alice", name="Alice", partner_id="bob"),
                GuestIn(id="bob", name="Bob", partner_id="alice"),
                GuestIn(id="carol", name="Carol", partner_id="dave"),
                GuestIn(id="dave", name="Dave", partner_id="carol"),
            ],
            options=SolveOptions(allow_empty_seats=False),
        )

        response = solve_seating(request)

        assert response.status in ("OPTIMAL", "FEASIBLE")

        # Check each pair
        for pair in [("alice", "bob"), ("carol", "dave")]:
            p1, p2 = pair
            p1_table = None
            p2_table = None
            p1_seat = None
            p2_seat = None

            for table in response.tables:
                for seat in table.seats:
                    if seat.guest_id == p1:
                        p1_table = table.table_id
                        p1_seat = seat.seat_index
                    elif seat.guest_id == p2:
                        p2_table = table.table_id
                        p2_seat = seat.seat_index

            # Same table
            assert p1_table == p2_table, f"{p1} and {p2} not at same table"

            # Adjacent
            assert p1_seat is not None and p2_seat is not None
            # Get capacity of their table
            table_cap = next(t.capacity for t in request.tables if t.id == p1_table)
            is_adjacent = (p1_seat + 1) % table_cap == p2_seat or (
                p1_seat - 1
            ) % table_cap == p2_seat
            assert is_adjacent, f"{p1} and {p2} not adjacent"


class TestPartnerValidation:
    """Tests for partner relationship validation."""

    def test_self_partner_rejected(self) -> None:
        """Self-partnering raises error."""
        request = OptimizeRequest(
            tables=[TableIn(id="t1", capacity=4)],
            guests=[
                GuestIn(id="alice", name="Alice", partner_id="alice"),
            ],
        )

        with pytest.raises(PartnerCycleError):
            solve_seating(request)

    def test_asymmetric_partner_rejected(self) -> None:
        """Asymmetric partner relationship raises error."""
        request = OptimizeRequest(
            tables=[TableIn(id="t1", capacity=4)],
            guests=[
                GuestIn(id="alice", name="Alice", partner_id="bob"),
                GuestIn(id="bob", name="Bob"),  # No partner_id back to alice
            ],
        )

        with pytest.raises(AsymmetricPartnerError):
            solve_seating(request)
