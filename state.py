"""Small physics data structures in meters, seconds, and kilograms."""

from dataclasses import dataclass
import math


def _finite(name: str, value: float) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a finite number")
    if not math.isfinite(value):
        raise ValueError(f"{name} must be a finite number")


@dataclass(frozen=True)
class PhysicsParameters:
    radius: float = 0.2
    mass: float = 1.0
    gravity: float = 9.81
    restitution: float = 0.8
    dt: float = 1.0 / 240.0

    def __post_init__(self) -> None:
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
    width: float = 4.0
    height: float = 3.0

    def __post_init__(self) -> None:
        for name in ("width", "height"):
            _finite(name, getattr(self, name))
            if getattr(self, name) <= 0:
                raise ValueError(f"{name} must be positive")

    def validate_for(self, parameters: PhysicsParameters) -> None:
        """Check geometry against the selected radius, without constraining state."""
        if min(self.width, self.height) <= 2 * parameters.radius:
            raise ValueError("box width and height must exceed the circle diameter")


@dataclass
class CircleState:
    x: float = 1.0
    y: float = 2.0
    vx: float = 1.5
    vy: float = 0.0
    step_count: int = 0

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        """Allow any finite position, including penetration and above-box states."""
        for name in ("x", "y", "vx", "vy"):
            _finite(name, getattr(self, name))
        if type(self.step_count) is not int or self.step_count < 0:
            raise ValueError("step_count must be a nonnegative integer")

    def time(self, parameters: PhysicsParameters) -> float:
        """Elapsed seconds; keep the same fixed dt throughout a trajectory."""
        return self.step_count * parameters.dt
