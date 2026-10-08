"""Advance scalar physics state with velocity-first semi-implicit Euler.

Notes
-----
step is contact-free; complete_step integrates and then resolves contacts.
Both mutate the supplied state. See assign3/SPEC.md [EQ-STEP] and
[EQ-TIME]. No GUI, plotting, or file output is performed.
"""

from contacts import ContactRecord, resolve_contacts
from state import Box, CircleState, PhysicsParameters


def step(state: CircleState, parameters: PhysicsParameters) -> None:
    """Advance state by one contact-free, velocity-first Euler step.

    Parameters
    ----------
    state : CircleState
        Mutable scalar position (m), velocity (m/s), and step count.
    parameters : PhysicsParameters
        Supplies gravity in m/s^2 and positive fixed dt in s.

    Returns
    -------
    None
        The input state is updated; no new state is returned.

    Notes
    -----
    Callers must supply valid state and parameters; this function does not
    validate them or check arithmetic results for finiteness. In order, it
    subtracts gravity * dt from vy, advances x with vx, advances y with the
    new vy, and increments step_count once. vx is unchanged. No contacts
    are resolved. See assign3/SPEC.md [EQ-STEP], [EQ-TIME], and [EQ-DRIFT].

    Examples
    --------
    >>> from state import CircleState, PhysicsParameters
    >>> from integration import step
    >>> state = CircleState(vy=3.0, step_count=7)
    >>> result = step(state, PhysicsParameters(dt=0.1))
    >>> result is None
    True
    >>> (round(state.x, 6), round(state.y, 6), round(state.vy, 6))
    (1.15, 2.2019, 2.019)
    >>> (state.vx, state.step_count)
    (1.5, 8)
    """
    state.vy -= parameters.gravity * parameters.dt
    state.x += state.vx * parameters.dt
    state.y += state.vy * parameters.dt
    state.step_count += 1


def complete_step(
    state: CircleState, parameters: PhysicsParameters, box: Box
) -> list[ContactRecord]:
    """Integrate once, then correct floor and side-wall contacts.

    Parameters
    ----------
    state : CircleState
        Mutable center position in m, velocity in m/s, and step count.
    parameters : PhysicsParameters
        Valid physical parameters with fixed positive dt in s.
    box : Box
        Geometry in m; both dimensions must exceed the circle diameter.

    Returns
    -------
    list of ContactRecord
        Detected contacts in floor, left, right order, possibly empty.
        Each record contains signed correction and normal velocities.

    Raises
    ------
    ValueError
        If box.validate_for rejects the geometry before integration.

    Notes
    -----
    Mutates state through step and resolve_contacts. The count increments
    once before contact detection; resolution does not advance time again.
    State finiteness is not checked here. There is no resting-contact cutoff;
    small repeated floor rebounds can persist. See assign3/SPEC.md [EQ-STEP],
    [EQ-FLOOR], [EQ-LEFT], [EQ-RIGHT], and [EQ-MICROBOUNCE].
    """
    box.validate_for(parameters)  # Reject invalid geometry before mutating state.
    step(state, parameters)
    return resolve_contacts(state, parameters, box)
