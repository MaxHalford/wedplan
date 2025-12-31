#!/usr/bin/env python3
"""Burner script to test adjacent group constraints in the solver.

This script verifies that:
1. Groups of 2 (pair) sit adjacent
2. Groups of 3 sit in contiguous seats
3. Groups of 4 sit in contiguous seats
4. Multiple groups all maintain contiguity
5. Error handling works for invalid inputs

Run with:
    source ./venv/bin/activate && python scratch/experiment_adjacent_groups.py
"""

from wedplan.domain.errors import (
    DuplicateGroupMemberError,
    GroupTooLargeError,
    GuestNotFoundError,
)
from wedplan.domain.models import AdjacentGroup, GuestIn, OptimizeRequest, TableIn
from wedplan.solver.cp_sat import solve_seating


def are_contiguous(seats: list[int], capacity: int) -> bool:
    """Check if seat indices form a contiguous block around circular table."""
    if len(seats) <= 1:
        return True

    sorted_seats = sorted(seats)

    # Check normal contiguous (no wrap)
    normal_contiguous = all(sorted_seats[i + 1] - sorted_seats[i] == 1 for i in range(len(sorted_seats) - 1))
    if normal_contiguous:
        return True

    # Check wrap-around contiguous
    gaps = []
    for i in range(len(sorted_seats) - 1):
        gaps.append(sorted_seats[i + 1] - sorted_seats[i])
    wrap_gap = capacity - sorted_seats[-1] + sorted_seats[0]
    gaps.append(wrap_gap)

    large_gaps = [g for g in gaps if g > 1]
    return len(large_gaps) <= 1


def test_pair_contiguous() -> None:
    """Test that a pair sits adjacent."""
    print("=" * 60)
    print("TEST: Pair (2 guests) must sit adjacent")
    print("=" * 60)

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
    print(f"Status: {response.status}")

    table = response.tables[0]
    seats_by_guest = {s.guest_id: s.seat_index for s in table.seats if s.guest_id}

    alice_seat = seats_by_guest["alice"]
    bob_seat = seats_by_guest["bob"]

    cap = len(table.seats)
    is_adj = (alice_seat + 1) % cap == bob_seat or (alice_seat - 1) % cap == bob_seat

    print(f"Alice at seat {alice_seat}, Bob at seat {bob_seat}")
    print(f"Adjacent: {is_adj}")
    print(f"All seats: {seats_by_guest}")
    assert is_adj, "FAIL: Alice and Bob not adjacent!"
    print("PASS!\n")


def test_group_of_three() -> None:
    """Test that a group of 3 sits contiguously."""
    print("=" * 60)
    print("TEST: Group of 3 must sit contiguously")
    print("=" * 60)

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
    print(f"Status: {response.status}")

    table = response.tables[0]
    seats_by_guest = {s.guest_id: s.seat_index for s in table.seats if s.guest_id}

    group_seats = [
        seats_by_guest["alice"],
        seats_by_guest["bob"],
        seats_by_guest["carol"],
    ]

    cap = len(table.seats)
    contiguous = are_contiguous(group_seats, cap)

    print(f"Group seats: {group_seats}")
    print(f"Contiguous: {contiguous}")
    print(f"All seats: {seats_by_guest}")
    assert contiguous, "FAIL: Group not contiguous!"
    print("PASS!\n")


def test_group_of_four() -> None:
    """Test that a group of 4 sits contiguously."""
    print("=" * 60)
    print("TEST: Group of 4 must sit contiguously")
    print("=" * 60)

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
    print(f"Status: {response.status}")

    table = response.tables[0]
    seats_by_guest = {s.guest_id: s.seat_index for s in table.seats if s.guest_id}

    group_seats = [
        seats_by_guest["g1"],
        seats_by_guest["g2"],
        seats_by_guest["g3"],
        seats_by_guest["g4"],
    ]

    cap = len(table.seats)
    contiguous = are_contiguous(group_seats, cap)

    print(f"Group seats: {group_seats}")
    print(f"Contiguous: {contiguous}")
    print(f"All seats: {seats_by_guest}")
    assert contiguous, "FAIL: Group not contiguous!"
    print("PASS!\n")


def test_multiple_groups() -> None:
    """Test that multiple groups each form contiguous blocks."""
    print("=" * 60)
    print("TEST: Multiple groups each form contiguous blocks")
    print("=" * 60)

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
    print(f"Status: {response.status}")

    table = response.tables[0]
    seats_by_guest = {s.guest_id: s.seat_index for s in table.seats if s.guest_id}
    cap = len(table.seats)

    a_seats = [seats_by_guest["a1"], seats_by_guest["a2"], seats_by_guest["a3"]]
    b_seats = [seats_by_guest["b1"], seats_by_guest["b2"]]

    a_contiguous = are_contiguous(a_seats, cap)
    b_contiguous = are_contiguous(b_seats, cap)

    print(f"Group A seats: {a_seats}, contiguous: {a_contiguous}")
    print(f"Group B seats: {b_seats}, contiguous: {b_contiguous}")
    print(f"All seats: {seats_by_guest}")

    assert a_contiguous, "FAIL: Group A not contiguous!"
    assert b_contiguous, "FAIL: Group B not contiguous!"
    print("PASS!\n")


def test_validation_errors() -> None:
    """Test that validation errors are raised correctly."""
    print("=" * 60)
    print("TEST: Validation errors")
    print("=" * 60)

    # Test unknown guest
    try:
        request = OptimizeRequest(
            tables=[TableIn(id="t1", capacity=4)],
            guests=[GuestIn(id="alice", name="Alice")],
            adjacent_groups=[AdjacentGroup(guest_ids=["alice", "unknown"])],
        )
        solve_seating(request)
        print("FAIL: Should have raised GuestNotFoundError")
    except GuestNotFoundError as e:
        print(f"GuestNotFoundError correctly raised: {e}")

    # Test duplicate guest in group
    try:
        request = OptimizeRequest(
            tables=[TableIn(id="t1", capacity=4)],
            guests=[
                GuestIn(id="alice", name="Alice"),
                GuestIn(id="bob", name="Bob"),
            ],
            adjacent_groups=[AdjacentGroup(guest_ids=["alice", "alice", "bob"])],
        )
        solve_seating(request)
        print("FAIL: Should have raised DuplicateGroupMemberError")
    except DuplicateGroupMemberError as e:
        print(f"DuplicateGroupMemberError correctly raised: {e}")

    # Test group too large
    try:
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
        solve_seating(request)
        print("FAIL: Should have raised GroupTooLargeError")
    except GroupTooLargeError as e:
        print(f"GroupTooLargeError correctly raised: {e}")

    print("PASS!\n")


def main() -> None:
    """Run all tests."""
    print("\n" + "=" * 60)
    print("ADJACENT GROUPS SOLVER TEST")
    print("=" * 60 + "\n")

    test_pair_contiguous()
    test_group_of_three()
    test_group_of_four()
    test_multiple_groups()
    test_validation_errors()

    print("=" * 60)
    print("ALL TESTS PASSED!")
    print("=" * 60)


if __name__ == "__main__":
    main()
