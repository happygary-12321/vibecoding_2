"""Define scalar physics state and parameter dataclasses in SI units.

Notes
-----
Positions describe the circle center, with x rightward and y upward.
See assign3/SPEC.md [EQ-MOTION], [EQ-STEP], and [EQ-TIME]. Constructors
check numeric fields; later mutation of CircleState requires explicit
validation. This module performs no integration or rendering.
"""

from dataclasses import dataclass
import math


def _finite(name: str, value: float) -> None:
    """Check a scalar field's type and finiteness.

    Use this type/finiteness gate before a field-specific range check.
    Boolean values are rejected even though bool is an int subclass.

    Parameters
    ----------
    name : str
        Field name included in error messages.
    value : int or float
        Scalar to inspect; bool is rejected.

    Returns
    -------
    None
        The value is not converted or modified.

    Raises
    ------
    ValueError
        If the type is rejected or the numeric value is nonfinite.
    OverflowError
        If math.isfinite cannot convert an excessively large integer.

    See Also
    --------
    state.PhysicsParameters : Apply physical range checks after finiteness validation.

    Examples
    --------
    >>> from state import _finite
    >>> _finite('mass', 1.0) is None
    True
    >>> _finite('mass', True)
    Traceback (most recent call last):
    ...
    ValueError: mass must be a finite number
    """
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a finite number")
    if not math.isfinite(value):
        raise ValueError(f"{name} must be a finite number")


@dataclass(frozen=True)
class PhysicsParameters:
    """Hold frozen physical constants and a fixed integration timestep.

    Create one parameter object per fixed-timestep trajectory. Its frozen
    fields separate physical constants from the mutable circle state.

    Parameters
    ----------
    radius : float, optional
        Positive circle radius in m; default 0.2.
    mass : float, optional
        Positive mass in kg; default 1.0.
    gravity : float, optional
        Nonnegative downward acceleration magnitude in m/s^2; default 9.81.
    restitution : float, optional
        Dimensionless coefficient in [0, 1]; default 0.8.
    dt : float, optional
        Positive fixed timestep in s; default 1/240.

    Attributes
    ----------
    radius, mass, gravity, restitution, dt : float
        Frozen scalar fields with the units and defaults above. Python int
        values passing finiteness/range checks are retained; bool is rejected.

    Raises
    ------
    ValueError
        If a field has a rejected type, is nonfinite, or violates its range.
    OverflowError
        If finiteness checking cannot convert an excessively large integer.

    See Also
    --------
    state.Box.validate_for : Check that a box accommodates the chosen radius.

    Notes
    -----
    Geometry compatibility is checked separately by Box.validate_for.
    Gravity is subtracted from vertical velocity in assign3/SPEC.md
    [EQ-STEP]; restitution follows [EQ-NORMAL]. Keep dt fixed per trajectory.

    Examples
    --------
    >>> from state import Box, CircleState, PhysicsParameters
    >>> p = PhysicsParameters(restitution=0, dt=0.01)
    >>> (p.restitution, p.dt, p.gravity)
    (0, 0.01, 9.81)
    """
    radius: float = 0.2
    mass: float = 1.0
    gravity: float = 9.81
    restitution: float = 0.8
    dt: float = 1.0 / 240.0

    def __post_init__(self) -> None:
        """Validate physical scalar fields after dataclass initialization.

        Dataclass construction invokes this hook automatically. Recalling the
        hook performs the same validation without advancing simulation time.

        Returns
        -------
        None
            No field is converted or modified.

        Raises
        ------
        ValueError
            If a scalar fails type, finiteness, or physical range checks.
        OverflowError
            If an integer is too large for the finiteness check.

        See Also
        --------
        state.PhysicsParameters : Construct the object and trigger this validation.

        Examples
        --------
        >>> from state import Box, CircleState, PhysicsParameters
        >>> value = PhysicsParameters()
        >>> value.__post_init__() is None
        True
        """
        for name in ("radius", "mass", "gravity", "restitution", "dt"):
            _finite(name, getattr(self, name))
        for name in ("radius", "mass", "dt"):
            if getattr(self, name) <= 0:
                raise ValueError(f"{name} must be positive")
        if self.gravity < 0:
            raise ValueError("gravity must be nonnegative")
        if not 0 <= self.restitution <= 1:
            raise ValueError("restitution must be in [0, 1]")


@dataclass(frozen=True)
class Box:
    """Hold frozen box dimensions in meters.

    Dimensions define the floor and displayed sides. The height participates
    in geometry validation but does not create a ceiling collision.

    Parameters
    ----------
    width : float, optional
        Positive finite width in m; default 4.0.
    height : float, optional
        Positive finite displayed wall height in m; default 3.0.

    Attributes
    ----------
    width, height : float
        Frozen dimensions; int values passing finiteness/range checks are
        retained without conversion. Bool values are rejected.

    Raises
    ------
    ValueError
        If a dimension has a rejected type, is nonfinite, or is nonpositive.
    OverflowError
        If an integer cannot be converted for the finiteness check.

    See Also
    --------
    contacts.resolve_contacts : Apply floor and side-wall bounds to a state.

    Notes
    -----
    Construction does not check the circle diameter. Call validate_for for
    that check. Height does not create a ceiling or limit side-wall contact
    checks; see assign3/SPEC.md [EQ-FLOOR], [EQ-LEFT], and [EQ-RIGHT].

    Examples
    --------
    >>> from state import Box, CircleState, PhysicsParameters
    >>> box = Box(width=2, height=1)
    >>> box.validate_for(PhysicsParameters(radius=0.2)) is None
    True
    """
    width: float = 4.0
    height: float = 3.0

    def __post_init__(self) -> None:
        """Check finite positive dimensions after dataclass initialization.

        Dataclass construction invokes this hook automatically. Recalling the
        hook performs the same validation without advancing simulation time.

        Returns
        -------
        None
            Dimensions are not converted or modified.

        Raises
        ------
        ValueError
            If a dimension fails type, finiteness, or positivity checks.
        OverflowError
            If an integer is too large for the finiteness check.

        See Also
        --------
        state.Box : Construct the object and trigger this validation.

        Examples
        --------
        >>> from state import Box, CircleState, PhysicsParameters
        >>> value = Box()
        >>> value.__post_init__() is None
        True
        """
        for name in ("width", "height"):
            _finite(name, getattr(self, name))
            if getattr(self, name) <= 0:
                raise ValueError(f"{name} must be positive")

    def validate_for(self, parameters: PhysicsParameters) -> None:
        """Check both box dimensions against a selected circle diameter.

        Call this after selecting both geometry and radius. A box can be valid
        on its own while too small for a particular circle.

        Parameters
        ----------
        parameters : PhysicsParameters
            Supplies radius in m; callers must provide valid parameters.

        Returns
        -------
        None
            Geometry is unchanged.

        Raises
        ------
        ValueError
            If width or height is less than or equal to twice the radius.

        See Also
        --------
        state.Box : Validate positive dimensions independently of radius.

        Notes
        -----
        This check does not constrain state positions or introduce a ceiling.
        See assign3/SPEC.md [EQ-LEFT] and [EQ-RIGHT].

        Examples
        --------
        >>> from state import Box, CircleState, PhysicsParameters
        >>> Box(width=0.4).validate_for(PhysicsParameters())
        Traceback (most recent call last):
        ...
        ValueError: box width and height must exceed the circle diameter
        """
        if min(self.width, self.height) <= 2 * parameters.radius:
            raise ValueError("box width and height must exceed the circle diameter")


@dataclass
class CircleState:
    """Store mutable circle-center motion and an integer step count.

    Store the center and velocity for in-place advancement. Construction
    checks numeric state, while later field assignments remain mutable.

    Parameters
    ----------
    x, y : float, optional
        Finite center coordinates in m; defaults 1.0 and 2.0.
    vx, vy : float, optional
        Finite velocities in m/s; defaults 1.5 and 0.0.
    step_count : int, optional
        Nonnegative count with exact Python int type; default 0.

    Attributes
    ----------
    x, y : float
        Mutable center coordinates in m, with x rightward and y upward.
    vx, vy : float
        Mutable velocities in m/s.
    step_count : int
        Mutable dimensionless count used to compute simulation time.

    Raises
    ------
    ValueError
        If construction fails validate: rejected scalar type, nonfinite
        value, or invalid count.
    OverflowError
        If a scalar integer is too large for finiteness checking.

    See Also
    --------
    integration.complete_step : Advance this state and then resolve contacts.

    Notes
    -----
    Int coordinates/velocities passing finiteness checks are retained without
    coercion; bool is rejected. Penetration and above-box positions are legal.
    Assignments after construction are not automatically validated.
    See assign3/SPEC.md [EQ-STEP] and [EQ-TIME].

    Examples
    --------
    >>> from state import Box, CircleState, PhysicsParameters
    >>> state = CircleState(y=0.1, vy=2)
    >>> (state.y, state.vy, state.step_count)
    (0.1, 2, 0)
    """
    x: float = 1.0
    y: float = 2.0
    vx: float = 1.5
    vy: float = 0.0
    step_count: int = 0

    def __post_init__(self) -> None:
        """Validate state immediately after dataclass initialization.

        Dataclass construction invokes this hook automatically. Recalling the
        hook performs the same validation without advancing simulation time.

        Returns
        -------
        None
            Fields are unchanged.

        Raises
        ------
        ValueError
            If validate rejects the coordinates, velocities, or count.
        OverflowError
            If a scalar integer is too large for finiteness checking.

        See Also
        --------
        state.CircleState : Construct the object and trigger this validation.

        Examples
        --------
        >>> from state import Box, CircleState, PhysicsParameters
        >>> value = CircleState()
        >>> value.__post_init__() is None
        True
        """
        self.validate()

    def validate(self) -> None:
        """Check scalar finiteness and the nonnegative integer count.

        Recheck a state after manual mutation. This tests scalar validity and
        the step count, without projecting coordinates onto any boundary.

        Returns
        -------
        None
            State is inspected without mutation.

        Raises
        ------
        ValueError
            If coordinates or velocities are not finite int/float values
            excluding bool, or step_count is not an exact nonnegative int.
        OverflowError
            If a scalar integer is too large for finiteness checking.

        See Also
        --------
        contacts.resolve_contacts : Correct geometric overlap after validation.

        Notes
        -----
        Positions need not be inside the box. This does not resolve contacts;
        see assign3/SPEC.md [EQ-FLOOR], [EQ-LEFT], and [EQ-RIGHT].

        Examples
        --------
        >>> from state import Box, CircleState, PhysicsParameters
        >>> state = CircleState()
        >>> state.step_count = -1
        >>> state.validate()
        Traceback (most recent call last):
        ...
        ValueError: step_count must be a nonnegative integer
        """
        for name in ("x", "y", "vx", "vy"):
            _finite(name, getattr(self, name))
        if type(self.step_count) is not int or self.step_count < 0:
            raise ValueError("step_count must be a nonnegative integer")

    def time(self, parameters: PhysicsParameters) -> float:
        """Compute elapsed simulation time from the current step count.

        Elapsed time is reconstructed from the count and the supplied timestep;
        changing dt retrospectively changes this reported time.

        Parameters
        ----------
        parameters : PhysicsParameters
            Supplies the fixed dt in s. Use the same dt for the whole trajectory.

        Returns
        -------
        float or int
            Scalar time in s, equal to step_count * dt.

        See Also
        --------
        integration.step : Increment the count during a contact-free step.

        Notes
        -----
        No state is changed or revalidated, and prior timestep values are not
        stored. See assign3/SPEC.md [EQ-TIME].

        Examples
        --------
        >>> from state import CircleState, PhysicsParameters
        >>> state = CircleState(step_count=12)
        >>> parameters = PhysicsParameters(dt=0.01)
        >>> round(state.time(parameters), 6)
        0.12
        >>> state.step_count
        12
        """
        return self.step_count * parameters.dt
