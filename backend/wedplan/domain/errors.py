"""Typed exception hierarchy for wedding seating optimization."""


class WedplanError(Exception):
    """Base exception for all wedplan errors."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class ValidationError(WedplanError):
    """Domain validation error (distinct from Pydantic validation)."""


class GuestNotFoundError(ValidationError):
    """Referenced guest ID does not exist."""

    def __init__(self, guest_id: str, context: str) -> None:
        self.guest_id = guest_id
        super().__init__(f"Guest '{guest_id}' not found in {context}")


class TableNotFoundError(ValidationError):
    """Referenced table ID does not exist."""

    def __init__(self, table_id: str) -> None:
        self.table_id = table_id
        super().__init__(f"Table '{table_id}' not found")


class DuplicateIdError(ValidationError):
    """Duplicate ID detected where uniqueness is required."""

    def __init__(self, entity_type: str, entity_id: str) -> None:
        self.entity_type = entity_type
        self.entity_id = entity_id
        super().__init__(f"Duplicate {entity_type} ID: '{entity_id}'")


class PartnerCycleError(ValidationError):
    """Invalid partner relationship detected (e.g., self-partner)."""

    def __init__(self, guest_id: str, partner_id: str) -> None:
        self.guest_id = guest_id
        self.partner_id = partner_id
        super().__init__(
            f"Invalid partner relationship: guest '{guest_id}' "
            f"with partner '{partner_id}'"
        )


class AsymmetricPartnerError(ValidationError):
    """Partner relationship is not symmetric."""

    def __init__(self, guest_a: str, guest_b: str) -> None:
        self.guest_a = guest_a
        self.guest_b = guest_b
        super().__init__(
            f"Asymmetric partner: '{guest_a}' -> '{guest_b}' but "
            f"'{guest_b}' does not reference '{guest_a}'"
        )


class CapacityError(ValidationError):
    """Capacity constraint violation."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


class SolverError(WedplanError):
    """Error during solver execution."""


class ModelBuildError(SolverError):
    """Error while building the CP-SAT model."""


class InfeasibleError(SolverError):
    """The optimization problem has no feasible solution."""

    def __init__(self) -> None:
        super().__init__("No feasible seating arrangement exists for given constraints")
