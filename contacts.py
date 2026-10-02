"""Discrete floor and side-wall contact resolution in SI units."""

from dataclasses import dataclass

from state import Box, CircleState, PhysicsParameters


@dataclass(frozen=True)
class ContactRecord:
    surface: str
    position_correction: tuple[float, float]  # Signed (dx, dy), meters.
    normal_velocity_before: float  # m/s; positive points into allowed region.
    normal_velocity_after: float

    @property
    def is_impact(self) -> bool:
        """True only when this response actually changed normal velocity."""
        return self.normal_velocity_before != self.normal_velocity_after


def resolve_contacts(
    state: CircleState, parameters: PhysicsParameters, box: Box
) -> list[ContactRecord]:
    """Correct contacts in floor/left/right order without advancing time.

    Normal directions are +y at the floor, +x at the left wall, and -x at
    the right wall. Touching counts as contact, even with no velocity change.
    """
    box.validate_for(parameters)
    radius, restitution = parameters.radius, parameters.restitution
    records = []

    if state.y <= radius:
        correction, before = radius - state.y, state.vy
        state.y = radius
        if state.vy < 0:
            state.vy = -restitution * state.vy
        records.append(ContactRecord("floor", (0.0, correction), before, state.vy))

    if state.x <= radius:
        correction, before = radius - state.x, state.vx
        state.x = radius
        if state.vx < 0:
            state.vx = -restitution * state.vx
        records.append(ContactRecord("left", (correction, 0.0), before, state.vx))

    right = box.width - radius
    if state.x >= right:
        correction, before = right - state.x, -state.vx
        state.x = right
        if state.vx > 0:
            state.vx = -restitution * state.vx
        records.append(ContactRecord("right", (correction, 0.0), before, -state.vx))

    return records
