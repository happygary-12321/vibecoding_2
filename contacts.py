"""Resolve discrete circle contacts with a floor and two side walls.

Notes
-----
The resolver mutates scalar SI state and emits frozen contact records.
There is no ceiling or side-wall height test. See assign3/SPEC.md
[EQ-NORMAL], [EQ-FLOOR], [EQ-LEFT], and [EQ-RIGHT].
"""

from dataclasses import dataclass

from state import Box, CircleState, PhysicsParameters


@dataclass(frozen=True)
class ContactRecord:
    """Store a frozen record of one detected contact.

    A record distinguishes touching/projection from a velocity-changing
    impact. Normal signs are defined relative to each allowed half-plane.

    Parameters
    ----------
    surface : str
        Resolver-emitted name: 'floor', 'left', or 'right'.
    position_correction : tuple of float
        Two-element (dx, dy) signed displacement in m.
    normal_velocity_before : float
        Scalar normal velocity in m/s before response.
    normal_velocity_after : float
        Scalar normal velocity in m/s after response.

    Attributes
    ----------
    surface : str
        Contact surface name.
    position_correction : tuple of float
        Frozen two-element signed position correction in m.
    normal_velocity_before, normal_velocity_after : float
        Frozen scalar velocities in m/s; positive points into the region.
    is_impact : bool
        Whether the two stored normal velocity values compare unequal.

    See Also
    --------
    contacts.resolve_contacts : Create records while mutating circle state.

    Notes
    -----
    The dataclass performs no value/type validation. Normals are +y, +x,
    and -x for floor, left, and right. Records include touching contacts
    and position-only corrections. See assign3/SPEC.md [EQ-NORMAL].

    Examples
    --------
    >>> from contacts import ContactRecord
    >>> record = ContactRecord('floor', (0.0, 0.05), 2.0, 2.0)
    >>> (record.position_correction, record.is_impact)
    ((0.0, 0.05), False)
    """
    surface: str
    position_correction: tuple[float, float]  # Signed (dx, dy), meters.
    normal_velocity_before: float  # m/s; positive points into allowed region.
    normal_velocity_after: float

    @property
    def is_impact(self) -> bool:
        """Compare the stored before and after normal velocities.

        Use this flag to count velocity-changing responses. A nonzero position
        correction alone does not make the recorded contact an impact.

        Returns
        -------
        bool
            True exactly when normal_velocity_before != normal_velocity_after.

        See Also
        --------
        contacts.resolve_contacts : Record normal velocities before and after response.

        Notes
        -----
        This property does not test penetration, correction size, or force.
        Separating and zero-speed contacts emitted by the resolver have equal
        velocity values. See assign3/SPEC.md [EQ-NORMAL].

        Examples
        --------
        >>> from contacts import ContactRecord
        >>> ContactRecord('floor', (0.0, 0.05), 2.0, 2.0).is_impact
        False
        >>> ContactRecord('floor', (0.0, 0.0), -2.0, 1.6).is_impact
        True
        """
        return self.normal_velocity_before != self.normal_velocity_after


def resolve_contacts(
    state: CircleState, parameters: PhysicsParameters, box: Box
) -> list[ContactRecord]:
    """Correct detected floor and wall contacts without advancing time.

    Use direct resolution to project an overlapping state without a timestep.
    Separating overlaps are corrected without reversing the outgoing velocity.

    Parameters
    ----------
    state : CircleState
        Mutable center coordinates in m and velocities in m/s.
    parameters : PhysicsParameters
        Supplies positive radius in m and restitution in [0, 1].
    box : Box
        Geometry in m; both dimensions must exceed twice the radius.

    Returns
    -------
    list of ContactRecord
        Records in floor, left, right detection order; empty if no contact.
        Touching surfaces produce records even with zero correction.

    Raises
    ------
    ValueError
        If box.validate_for rejects the geometry.

    See Also
    --------
    integration.complete_step : Integrate first, then call this resolver.

    Notes
    -----
    Correct y <= radius, then x <= radius, then x >= width - radius.
    Reflect vy only if negative at the floor, vx only if negative at the
    left wall, and vx only if positive at the right wall. Separating and
    zero normal velocities and tangential components are preserved.
    Positions/velocities can change in place; step_count never changes.
    State finiteness and parameter validity are caller responsibilities.
    There is no ceiling, wall-height cutoff, or resting-contact threshold.
    See assign3/SPEC.md [EQ-FLOOR], [EQ-LEFT], [EQ-RIGHT], and [EQ-NORMAL].

    Examples
    --------
    >>> from state import Box, CircleState, PhysicsParameters
    >>> from contacts import resolve_contacts
    >>> state = CircleState(y=0.15, vy=2.0, step_count=5)
    >>> records = resolve_contacts(state, PhysicsParameters(), Box())
    >>> (round(state.y, 6), state.vy, state.step_count)
    (0.2, 2.0, 5)
    >>> [(record.surface, record.is_impact) for record in records]
    [('floor', False)]
    >>> tuple(round(value, 6) for value in records[0].position_correction)
    (0.0, 0.05)
    """
    box.validate_for(parameters)
    radius, restitution = parameters.radius, parameters.restitution
    records = []

    # Floor, left, right is also record order. At corners the floor and wall
    # change independent components; width > 2*radius keeps wall regions disjoint.
    # Reordering these responses changes record order, not the final state.
    # Lower edge y-radius <= 0 includes exact touch. Correct penetration even
    # when separating; velocity reversal is a separate decision.
    if state.y <= radius:
        correction, before = radius - state.y, state.vy
        state.y = radius
        # Only inward motion receives restitution; upward/zero vy is preserved.
        # No speed cutoff suppresses the small rebounds produced by later steps.
        if state.vy < 0:
            state.vy = -restitution * state.vy
        records.append(ContactRecord("floor", (0.0, correction), before, state.vy))

    # Left edge x-radius <= 0 includes touch; project even separating overlaps.
    # Negative vx enters this wall; tangential vy is unchanged.
    if state.x <= radius:
        correction, before = radius - state.x, state.vx
        state.x = radius
        if state.vx < 0:
            state.vx = -restitution * state.vx
        records.append(ContactRecord("left", (correction, 0.0), before, state.vx))

    # Right edge x+radius >= width includes touch. Its inward normal is -x:
    # records negate vx, while reflection requires positive vx into the wall.
    right = box.width - radius
    if state.x >= right:
        correction, before = right - state.x, -state.vx
        state.x = right
        if state.vx > 0:
            state.vx = -restitution * state.vx
        records.append(ContactRecord("right", (correction, 0.0), before, -state.vx))

    # Height is not a contact bound: no ceiling response exists, and side-wall
    # tests apply above the displayed upper guide as well.
    return records
