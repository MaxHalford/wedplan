"""ID-to-index mapping for guests and tables.

Maps string IDs to contiguous integer indices for efficient
use in the CP-SAT model.
"""

from dataclasses import dataclass, field

from wedplan.domain.errors import DuplicateIdError, GuestNotFoundError
from wedplan.domain.models import GroupIn, GuestIn, OptimizeRequest, TableIn


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
class GroupInfo:
    """Group metadata for solver.

    Attributes:
        id: Original string ID.
        index: Contiguous integer index.
        guest_indices: Tuple of guest indices in this group.
    """

    id: str
    index: int
    guest_indices: tuple[int, ...]


@dataclass(frozen=True)
class ProblemMapping:
    """Complete mapping from request IDs to solver indices.

    Attributes:
        tables: List of table info, indexed by table index.
        guests: List of guest info, indexed by guest index.
        groups: List of group info, indexed by group index.
        guest_id_to_index: Map from guest ID to index.
        table_id_to_index: Map from table ID to index.
        group_id_to_index: Map from group ID to index.
        total_seats: Sum of all table capacities.
    """

    tables: tuple[TableInfo, ...]
    guests: tuple[GuestInfo, ...]
    groups: tuple[GroupInfo, ...]
    guest_id_to_index: dict[str, int] = field(default_factory=dict)
    table_id_to_index: dict[str, int] = field(default_factory=dict)
    group_id_to_index: dict[str, int] = field(default_factory=dict)
    total_seats: int = 0

    @property
    def num_guests(self) -> int:
        """Number of guests."""
        return len(self.guests)

    @property
    def num_tables(self) -> int:
        """Number of tables."""
        return len(self.tables)

    @property
    def num_groups(self) -> int:
        """Number of groups."""
        return len(self.groups)


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


def _validate_unique_group_ids(groups: list[GroupIn]) -> None:
    """Validate that all group IDs are unique.

    Args:
        groups: List of groups.

    Raises:
        DuplicateIdError: If duplicate group ID found.
    """
    seen: set[str] = set()
    for group in groups:
        if group.id in seen:
            raise DuplicateIdError("group", group.id)
        seen.add(group.id)


def _build_group_info(
    groups: list[GroupIn],
    guest_id_to_index: dict[str, int],
) -> tuple[tuple[GroupInfo, ...], dict[str, int]]:
    """Build group info and mapping.

    Args:
        groups: List of groups from request.
        guest_id_to_index: Mapping from guest ID to index.

    Returns:
        Tuple of (group info tuple, group_id_to_index dict).

    Raises:
        GuestNotFoundError: If a group references unknown guest ID.
    """
    group_id_to_index: dict[str, int] = {}
    group_infos: list[GroupInfo] = []

    for i, group in enumerate(groups):
        # Validate all guest IDs exist
        guest_indices: list[int] = []
        for guest_id in group.guest_ids:
            if guest_id not in guest_id_to_index:
                raise GuestNotFoundError(guest_id, f"group '{group.id}'")
            guest_indices.append(guest_id_to_index[guest_id])

        group_id_to_index[group.id] = i
        group_infos.append(
            GroupInfo(
                id=group.id,
                index=i,
                guest_indices=tuple(guest_indices),
            )
        )

    return tuple(group_infos), group_id_to_index


def create_mapping(request: OptimizeRequest) -> ProblemMapping:
    """Create complete problem mapping from request.

    Validates all IDs and relationships, then builds contiguous
    index mappings for use in the solver.

    Args:
        request: Optimization request.

    Returns:
        Complete problem mapping.

    Raises:
        DuplicateIdError: If duplicate table, guest, or group ID.
        GuestNotFoundError: If a group references unknown guest ID.
    """
    # Validate uniqueness
    _validate_unique_ids(request.tables, "table")
    _validate_unique_ids(request.guests, "guest")
    _validate_unique_group_ids(request.groups)

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

    # Build group mapping
    groups, group_id_to_index = _build_group_info(request.groups, guest_id_to_index)

    total_seats = sum(t.capacity for t in request.tables)

    return ProblemMapping(
        tables=tables,
        guests=guests,
        groups=groups,
        guest_id_to_index=guest_id_to_index,
        table_id_to_index=table_id_to_index,
        group_id_to_index=group_id_to_index,
        total_seats=total_seats,
    )
