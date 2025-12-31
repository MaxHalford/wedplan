"""Test solver with small instances having known solutions."""

from fastapi.testclient import TestClient

from wedplan.api.main import app
from wedplan.domain.models import (
    AffinityEdgeIn,
    GuestIn,
    OptimizeRequest,
    SolveOptions,
    TableIn,
)
from wedplan.solver.cp_sat import solve_seating


class TestSolverSmallInstances:
    """Tests for solver with small problem instances."""

    def test_single_guest_single_table(self) -> None:
        """Single guest is assigned to single table."""
        request = OptimizeRequest(
            tables=[TableIn(id="t1", capacity=4)],
            guests=[GuestIn(id="g1", name="Alice")],
        )

        response = solve_seating(request)

        assert response.status in ("OPTIMAL", "FEASIBLE")
        assert len(response.tables) == 1
        assert response.tables[0].table_id == "t1"

        # Find Alice's seat
        alice_seats = [s for s in response.tables[0].seats if s.guest_id == "g1"]
        assert len(alice_seats) == 1
        assert alice_seats[0].guest_name == "Alice"

    def test_two_guests_with_affinity(self) -> None:
        """Two guests with high affinity are placed at same table."""
        request = OptimizeRequest(
            tables=[
                TableIn(id="t1", capacity=2),
                TableIn(id="t2", capacity=2),
            ],
            guests=[
                GuestIn(id="g1", name="Alice"),
                GuestIn(id="g2", name="Bob"),
            ],
            affinities=[
                AffinityEdgeIn(a="g1", b="g2", score=100),
            ],
        )

        response = solve_seating(request)

        assert response.status in ("OPTIMAL", "FEASIBLE")
        assert response.objective_value == 100

        # Both should be at same table
        alice_table = None
        bob_table = None
        for table in response.tables:
            for seat in table.seats:
                if seat.guest_id == "g1":
                    alice_table = table.table_id
                if seat.guest_id == "g2":
                    bob_table = table.table_id

        assert alice_table == bob_table

    def test_four_guests_maximize_affinity(self) -> None:
        """Solver maximizes total affinity across tables."""
        request = OptimizeRequest(
            tables=[
                TableIn(id="t1", capacity=2),
                TableIn(id="t2", capacity=2),
            ],
            guests=[
                GuestIn(id="a", name="A"),
                GuestIn(id="b", name="B"),
                GuestIn(id="c", name="C"),
                GuestIn(id="d", name="D"),
            ],
            affinities=[
                # A-B like each other (100), C-D like each other (100)
                # Cross-pairs have lower affinity
                AffinityEdgeIn(a="a", b="b", score=100),
                AffinityEdgeIn(a="c", b="d", score=100),
                AffinityEdgeIn(a="a", b="c", score=10),
                AffinityEdgeIn(a="b", b="d", score=10),
            ],
            options=SolveOptions(allow_empty_seats=False),
        )

        response = solve_seating(request)

        assert response.status in ("OPTIMAL", "FEASIBLE")
        # Optimal: A-B at one table, C-D at other = 200
        # Suboptimal: A-C at one, B-D at other = 20
        assert response.objective_value == 200


class TestSolverAPIEndpoint:
    """Tests for the /v1/optimize API endpoint."""

    def test_optimize_endpoint_success(self) -> None:
        """POST /v1/optimize returns valid response."""
        client = TestClient(app)

        response = client.post(
            "/v1/optimize",
            json={
                "tables": [{"id": "t1", "capacity": 4}],
                "guests": [
                    {"id": "g1", "name": "Alice"},
                    {"id": "g2", "name": "Bob"},
                ],
                "affinities": [{"a": "g1", "b": "g2", "score": 50}],
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ("OPTIMAL", "FEASIBLE")
        assert "tables" in data
        assert "solver_stats" in data

    def test_optimize_endpoint_validation_error(self) -> None:
        """POST /v1/optimize returns 422 for invalid input."""
        client = TestClient(app)

        # Empty tables list
        response = client.post(
            "/v1/optimize",
            json={
                "tables": [],
                "guests": [{"id": "g1", "name": "Alice"}],
            },
        )

        assert response.status_code == 422

    def test_optimize_endpoint_invalid_affinity_reference(self) -> None:
        """POST /v1/optimize returns 422 for invalid guest reference."""
        client = TestClient(app)

        response = client.post(
            "/v1/optimize",
            json={
                "tables": [{"id": "t1", "capacity": 4}],
                "guests": [{"id": "g1", "name": "Alice"}],
                "affinities": [{"a": "g1", "b": "nonexistent", "score": 50}],
            },
        )

        assert response.status_code == 422
        assert "nonexistent" in response.json()["detail"]
