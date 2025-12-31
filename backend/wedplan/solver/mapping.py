"""ID-to-index mapping for guests and tables.

Maps string IDs to contiguous integer indices for efficient
use in the CP-SAT model.
"""

from dataclasses import dataclass, field

from wedplan.domain.errors import (
    DuplicateIdError,
)
from wedplan.domain.models import GuestIn, OptimizeRequest, TableIn


@dataclass(frozen=True)
class TableInfo:
    """Table metadata for solver.

    Attributes:
        id: Original string ID.
        index: Contiguous integer index.
        capacity: Number of seats.
        label: Optional display label.
    """

    id: str
    index: int
    capacity: int
    label: str | None


@dataclass(frozen=True)
class GuestInfo:
    """Guest metadata for solver.

    Attributes:
        id: Original string ID.
        index: Contiguous integer index.
        name: Display name.
    """

    id: str
    index: int
    name: str


@dataclass(frozen=True)
class ProblemMapping:
    """Complete mapping from request IDs to solver indices.

    Attributes:
        tables: List of table info, indexed by table index.
        guests: List of guest info, indexed by guest index.
        guest_id_to_index: Map from guest ID to index.
        table_id_to_index: Map from table ID to index.
        total_seats: Sum of all table capacities.
    """

    tables: tuple[TableInfo, ...]
    guests: tuple[GuestInfo, ...]
    guest_id_to_index: dict[str, int] = field(default_factory=dict)
    table_id_to_index: dict[str, int] = field(default_factory=dict)
    total_seats: int = 0

    @property
    def num_guests(self) -> int:
        """Number of guests."""
        return len(self.guests)

    @property
    def num_tables(self) -> int:
        """Number of tables."""
        return len(self.tables)


def _validate_unique_ids(items: list[TableIn] | list[GuestIn], entity_type: str) -> None:
    """Validate that all IDs are unique.

    Args:
        items: List of items with 'id' attribute.
        entity_type: Type name for error messages.

    Raises:
        DuplicateIdError: If duplicate ID found.
    """
    seen: set[str] = set()
    for item in items:
        if item.id in seen:
            raise DuplicateIdError(entity_type, item.id)
        seen.add(item.id)


def _build_guest_id_map(guests: list[GuestIn]) -> dict[str, int]:
    """Build mapping from guest ID to index.

    Args:
        guests: List of guests.

    Returns:
        Dictionary mapping guest ID to contiguous index.
    """
    return {guest.id: i for i, guest in enumerate(guests)}


def create_mapping(request: OptimizeRequest) -> ProblemMapping:
    """Create complete problem mapping from request.

    Validates all IDs and relationships, then builds contiguous
    index mappings for use in the solver.

    Args:
        request: Optimization request.

    Returns:
        Complete problem mapping.

    Raises:
        DuplicateIdError: If duplicate table or guest ID.
    """
    # Validate uniqueness
    _validate_unique_ids(request.tables, "table")
    _validate_unique_ids(request.guests, "guest")

    # Build table mapping
    table_id_to_index = {t.id: i for i, t in enumerate(request.tables)}
    tables = tuple(
        TableInfo(
            id=t.id,
            index=i,
            capacity=t.capacity,
            label=t.label,
        )
        for i, t in enumerate(request.tables)
    )

    # Build guest mapping
    guest_id_to_index = _build_guest_id_map(request.guests)

    # Build guest info
    guests = tuple(
        GuestInfo(
            id=g.id,
            index=i,
            name=g.name,
        )
        for i, g in enumerate(request.guests)
    )

    total_seats = sum(t.capacity for t in request.tables)

    return ProblemMapping(
        tables=tables,
        guests=guests,
        guest_id_to_index=guest_id_to_index,
        table_id_to_index=table_id_to_index,
        total_seats=total_seats,
    )
