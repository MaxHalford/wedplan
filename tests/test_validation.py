"""Test Pydantic strict mode validation."""

import pytest
from pydantic import ValidationError

from wedplan.domain.models import (
    AffinityEdgeIn,
    GuestIn,
    OptimizeRequest,
    SolveOptions,
    TableIn,
)


class TestTableInValidation:
    """Tests for TableIn model validation."""

    def test_valid_table(self) -> None:
        """Valid table input is accepted."""
        table = TableIn(id="t1", capacity=6)
        assert table.id == "t1"
        assert table.capacity == 6

    def test_capacity_must_be_int(self) -> None:
        """Capacity must be integer, not float (strict mode)."""
        with pytest.raises(ValidationError) as exc_info:
            TableIn(id="t1", capacity=6.0)  # type: ignore[arg-type]

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["loc"] == ("capacity",)
        assert "int" in errors[0]["msg"].lower()

    def test_capacity_minimum(self) -> None:
        """Capacity must be at least 2."""
        with pytest.raises(ValidationError) as exc_info:
            TableIn(id="t1", capacity=1)

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["loc"] == ("capacity",)

    def test_id_must_be_string(self) -> None:
        """ID must be string, not int (strict mode)."""
        with pytest.raises(ValidationError):
            TableIn(id=123, capacity=6)  # type: ignore[arg-type]


class TestGuestInValidation:
    """Tests for GuestIn model validation."""

    def test_valid_guest(self) -> None:
        """Valid guest input is accepted."""
        guest = GuestIn(id="g1", name="Alice")
        assert guest.id == "g1"
        assert guest.name == "Alice"
        assert guest.partner_id is None

    def test_guest_with_partner(self) -> None:
        """Guest with partner reference is valid."""
        guest = GuestIn(id="g1", name="Alice", partner_id="g2")
        assert guest.partner_id == "g2"

    def test_name_must_be_string(self) -> None:
        """Name must be string (strict mode)."""
        with pytest.raises(ValidationError):
            GuestIn(id="g1", name=123)  # type: ignore[arg-type]


class TestAffinityEdgeInValidation:
    """Tests for AffinityEdgeIn model validation."""

    def test_valid_affinity(self) -> None:
        """Valid affinity edge is accepted."""
        edge = AffinityEdgeIn(a="g1", b="g2", score=10)
        assert edge.a == "g1"
        assert edge.b == "g2"
        assert edge.score == 10
        assert edge.adjacency_bonus is None

    def test_score_must_be_non_negative(self) -> None:
        """Score must be >= 0."""
        with pytest.raises(ValidationError):
            AffinityEdgeIn(a="g1", b="g2", score=-1)

    def test_score_must_be_int(self) -> None:
        """Score must be integer (strict mode)."""
        with pytest.raises(ValidationError):
            AffinityEdgeIn(a="g1", b="g2", score=10.5)  # type: ignore[arg-type]

    def test_adjacency_bonus_optional(self) -> None:
        """Adjacency bonus is optional."""
        edge = AffinityEdgeIn(a="g1", b="g2", score=10, adjacency_bonus=5)
        assert edge.adjacency_bonus == 5


class TestSolveOptionsValidation:
    """Tests for SolveOptions model validation."""

    def test_defaults(self) -> None:
        """Default options are valid."""
        opts = SolveOptions()
        assert opts.time_limit_seconds == 5.0
        assert opts.num_workers == 1
        assert opts.allow_empty_seats is True

    def test_time_limit_must_be_positive(self) -> None:
        """Time limit must be > 0."""
        with pytest.raises(ValidationError):
            SolveOptions(time_limit_seconds=0)

    def test_num_workers_must_be_positive_int(self) -> None:
        """Number of workers must be >= 1."""
        with pytest.raises(ValidationError):
            SolveOptions(num_workers=0)


class TestOptimizeRequestValidation:
    """Tests for OptimizeRequest model validation."""

    def test_minimal_valid_request(self) -> None:
        """Minimal valid request is accepted."""
        request = OptimizeRequest(
            tables=[TableIn(id="t1", capacity=4)],
            guests=[GuestIn(id="g1", name="Alice")],
        )
        assert len(request.tables) == 1
        assert len(request.guests) == 1
        assert request.affinities == []

    def test_tables_required(self) -> None:
        """At least one table is required."""
        with pytest.raises(ValidationError):
            OptimizeRequest(
                tables=[],
                guests=[GuestIn(id="g1", name="Alice")],
            )

    def test_guests_required(self) -> None:
        """At least one guest is required."""
        with pytest.raises(ValidationError):
            OptimizeRequest(
                tables=[TableIn(id="t1", capacity=4)],
                guests=[],
            )
