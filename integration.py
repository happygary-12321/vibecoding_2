"""Contact-free integration and a complete step with discrete contacts."""

from contacts import ContactRecord, resolve_contacts
from state import Box, CircleState, PhysicsParameters


def step(state: CircleState, parameters: PhysicsParameters) -> None:
    """Advance state in place by one fixed step without resolving contacts."""
    state.vy -= parameters.gravity * parameters.dt
    state.x += state.vx * parameters.dt
    state.y += state.vy * parameters.dt
    state.step_count += 1


def complete_step(
    state: CircleState, parameters: PhysicsParameters, box: Box
) -> list[ContactRecord]:
    """Integrate once, then resolve floor and walls; return contact records."""
    box.validate_for(parameters)  # Reject invalid geometry before mutating state.
    step(state, parameters)
    return resolve_contacts(state, parameters, box)
