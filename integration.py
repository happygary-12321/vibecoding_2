"""Contact-free semi-implicit Euler; no rendering or third-party dependencies."""

from state import CircleState, PhysicsParameters


def step(state: CircleState, parameters: PhysicsParameters) -> None:
    """Advance state in place by one fixed step. Contacts are not resolved yet."""
    state.vy -= parameters.gravity * parameters.dt
    state.x += state.vx * parameters.dt
    state.y += state.vy * parameters.dt
    state.step_count += 1
