"""ID-to-index mapping for guests and tables.

Maps string IDs to contiguous integer indices for efficient
use in the CP-SAT model.
"""

from dataclasses import dataclass, field

from wedplan.domain.errors import (
    DuplicateGroupMemberError,
    DuplicateIdError,
    GroupTooLargeError,
    GuestNotFoundError,
)
from wedplan.domain.models import AdjacentGroup, GuestIn, OptimizeRequest, TableIn


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
        adjacent_groups: Groups of guest indices that must sit contiguously.
        total_seats: Sum of all table capacities.
    """

    tables: tuple[TableInfo, ...]
    guests: tuple[GuestInfo, ...]
    guest_id_to_index: dict[str, int] = field(default_factory=dict)
    table_id_to_index: dict[str, int] = field(default_factory=dict)
    adjacent_groups: tuple[tuple[int, ...], ...] = field(default_factory=tuple)
    total_seats: int = 0

    @property
    def num_guests(self) -> int:
        """Number of guests."""
        return len(self.guests)

    @property
    def num_tables(self) -> int:
        """Number of tables."""
        return len(self.tables)


def _validate_unique_ids(
    items: list[TableIn] | list[GuestIn], entity_type: str
) -> None:
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


def _validate_adjacent_groups(
    groups: list[AdjacentGroup],
    id_to_index: dict[str, int],
    max_capacity: int,
) -> tuple[tuple[int, ...], ...]:
    """Validate and convert adjacent groups to index tuples.

    Validates:
    - All guest IDs exist
    - No duplicate guests within a group
    - Group size does not exceed max table capacity

    Args:
        groups: List of adjacent groups from request.
        id_to_index: Guest ID to index mapping.
        max_capacity: Maximum table capacity.

    Returns:
        Tuple of groups, each group is a tuple of guest indices.

    Raises:
        GuestNotFoundError: If guest ID not found.
        DuplicateGroupMemberError: If guest appears twice in same group.
        GroupTooLargeError: If group exceeds max table capacity.
    """
    result: list[tuple[int, ...]] = []

    for group in groups:
        # Check group size fits in at least one table
        if len(group.guest_ids) > max_capacity:
            raise GroupTooLargeError(len(group.guest_ids), max_capacity)

        # Validate and convert guest IDs to indices
        seen: set[str] = set()
        indices: list[int] = []

        for guest_id in group.guest_ids:
            if guest_id not in id_to_index:
                raise GuestNotFoundError(guest_id, "adjacent_group")

            if guest_id in seen:
                raise DuplicateGroupMemberError(guest_id)

            seen.add(guest_id)
            indices.append(id_to_index[guest_id])

        result.append(tuple(indices))

    return tuple(result)


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
        GuestNotFoundError: If guest reference invalid.
        DuplicateGroupMemberError: If guest appears twice in same group.
        GroupTooLargeError: If adjacent group exceeds max table capacity.
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

    # Compute max table capacity for group validation
    max_capacity = max(t.capacity for t in request.tables)

    # Validate adjacent groups
    adjacent_groups = _validate_adjacent_groups(
        request.adjacent_groups, guest_id_to_index, max_capacity
    )

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
        adjacent_groups=adjacent_groups,
        total_seats=total_seats,
    )
