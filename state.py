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
    """
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a finite number")
    if not math.isfinite(value):
        raise ValueError(f"{name} must be a finite number")


@dataclass(frozen=True)
class PhysicsParameters:
    """Hold frozen physical constants and a fixed integration timestep.

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

    Notes
    -----
    Geometry compatibility is checked separately by Box.validate_for.
    Gravity is subtracted from vertical velocity in assign3/SPEC.md
    [EQ-STEP]; restitution follows [EQ-NORMAL]. Keep dt fixed per trajectory.
    """
    radius: float = 0.2
    mass: float = 1.0
    gravity: float = 9.81
    restitution: float = 0.8
    dt: float = 1.0 / 240.0

    def __post_init__(self) -> None:
        """Validate physical scalar fields after dataclass initialization.

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

    Notes
    -----
    Construction does not check the circle diameter. Call validate_for for
    that check. Height does not create a ceiling or limit side-wall contact
    checks; see assign3/SPEC.md [EQ-FLOOR], [EQ-LEFT], and [EQ-RIGHT].
    """
    width: float = 4.0
    height: float = 3.0

    def __post_init__(self) -> None:
        """Check finite positive dimensions after dataclass initialization.

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
        """
        for name in ("width", "height"):
            _finite(name, getattr(self, name))
            if getattr(self, name) <= 0:
                raise ValueError(f"{name} must be positive")

    def validate_for(self, parameters: PhysicsParameters) -> None:
        """Check both box dimensions against a selected circle diameter.

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

        Notes
        -----
        This check does not constrain state positions or introduce a ceiling.
        See assign3/SPEC.md [EQ-LEFT] and [EQ-RIGHT].
        """
        if min(self.width, self.height) <= 2 * parameters.radius:
            raise ValueError("box width and height must exceed the circle diameter")


@dataclass
class CircleState:
    """Store mutable circle-center motion and an integer step count.

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

    Notes
    -----
    Int coordinates/velocities passing finiteness checks are retained without
    coercion; bool is rejected. Penetration and above-box positions are legal.
    Assignments after construction are not automatically validated.
    See assign3/SPEC.md [EQ-STEP] and [EQ-TIME].
    """
    x: float = 1.0
    y: float = 2.0
    vx: float = 1.5
    vy: float = 0.0
    step_count: int = 0

    def __post_init__(self) -> None:
        """Validate state immediately after dataclass initialization.

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
        """
        self.validate()

    def validate(self) -> None:
        """Check scalar finiteness and the nonnegative integer count.

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

        Notes
        -----
        Positions need not be inside the box. This does not resolve contacts;
        see assign3/SPEC.md [EQ-FLOOR], [EQ-LEFT], and [EQ-RIGHT].
        """
        for name in ("x", "y", "vx", "vy"):
            _finite(name, getattr(self, name))
        if type(self.step_count) is not int or self.step_count < 0:
            raise ValueError("step_count must be a nonnegative integer")

    def time(self, parameters: PhysicsParameters) -> float:
        """Compute elapsed simulation time from the current step count.

        Parameters
        ----------
        parameters : PhysicsParameters
            Supplies the fixed dt in s. Use the same dt for the whole trajectory.

        Returns
        -------
        float or int
            Scalar time in s, equal to step_count * dt.

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
