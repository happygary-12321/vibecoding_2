"""Check scalar state validation and contact-free Euler integration.

Notes
-----
The script guard requires Python 3.12.10 and prints interpreter details
before invoking unittest. Importing this module does not run its suite.
Tests use the standard library and do not open a GUI.
See assign3/SPEC.md [EQ-STEP], [EQ-TIME], [EQ-FLIGHT], and [EQ-DRIFT].
"""

import sys
import unittest

from integration import step
from state import Box, CircleState, PhysicsParameters


# Roundoff allowances for <=480 steps, far below the ~0.01 m Euler error.
POSITION_TOL = 1e-10  # meters
VELOCITY_TOL = 1e-10  # meters/second


class IntegrationChecks(unittest.TestCase):
    """Check scalar state validation and contact-free Euler integration.

    Parameters
    ----------
    methodName : str, optional
        unittest.TestCase method selector; inherited default is 'runTest'.

    Attributes
    ----------
    failureException : type of Exception
        Inherited assertion-failure exception class; defaults to AssertionError.
    longMessage : bool
        Inherited message-combination setting, True by default. Includes the
        standard assertion message alongside a supplied message.
    maxDiff : int or None
        Inherited limit on displayed assertion-diff length, 640 characters by
        default. None disables the limit for assertions that use this setting.

    Notes
    -----
    Inherits unittest.TestCase lifecycle and assertion state; no additional
    persistent data attributes are defined. Test methods create local states
    or fixtures and return None. See assign3/SPEC.md [EQ-STEP], [EQ-TIME],
    [EQ-FLIGHT], and [EQ-DRIFT].
    """
    def measured(self, label, actual, expected, tolerance):
        """Print and assert one absolute-tolerance comparison.

        Parameters
        ----------
        label : str
            Printed quantity label, including units where applicable.
        actual, expected : float
            Measured and reference scalar in the same units.
        tolerance : float
            Absolute allowance in those units.

        Returns
        -------
        None
            No comparison value is returned.

        Raises
        ------
        AssertionError
            If the absolute comparison fails.

        Notes
        -----
        Prints label, expected/measured values and tolerance to stdout,
        then checks the values with assertAlmostEqual.
        """
        print(f"{label}: expected={expected:.12g}, measured={actual:.12g}, "
              f"absolute tolerance={tolerance:g}", flush=True)
        self.assertAlmostEqual(actual, expected, delta=tolerance)

    def test_defaults_and_geometry(self):
        """Check defaults, legal penetration, and diameter-dependent geometry.

        Returns
        -------
        None
            Results are reported through unittest assertions.

        Raises
        ------
        AssertionError
            If an expected result is not satisfied; unittest records failures.

        Notes
        -----
        Constructs default and invalid geometry cases; expects exact defaults and
        ValueError for dimensions not exceeding the diameter.
        See assign3/SPEC.md [EQ-STEP], [EQ-TIME], [EQ-FLIGHT], and [EQ-DRIFT].
        """
        p, s, box = PhysicsParameters(), CircleState(), Box()
        self.assertEqual((p.radius, p.mass, p.gravity, p.restitution, p.dt),
                         (0.2, 1.0, 9.81, 0.8, 1 / 240))
        self.assertEqual((s.x, s.y, s.vx, s.vy, s.step_count), (1, 2, 1.5, 0, 0))
        self.assertEqual((box.width, box.height), (4, 3))
        box.validate_for(p)
        self.assertEqual(s.time(p), 0)
        CircleState(x=-1, y=-1)  # Deliberate penetration is legal data.
        CircleState(y=10)  # No ceiling constraint.
        for box in (Box(width=0.4), Box(height=0.3)):
            with self.assertRaises(ValueError):
                box.validate_for(p)

    def test_invalid_state_and_parameters(self):
        """Check rejected numeric values, ranges, and step-count types.

        Returns
        -------
        None
            Results are reported through unittest assertions.

        Raises
        ------
        AssertionError
            If an expected result is not satisfied; unittest records failures.

        Notes
        -----
        Constructs cases with nonfinite values, nonpositive dimensions/timestep,
        invalid restitution/gravity, and invalid counts; checks accepted endpoints.
        See assign3/SPEC.md [EQ-STEP], [EQ-TIME], [EQ-FLIGHT], and [EQ-DRIFT].
        """
        for constructor, fields in (
            (CircleState, ("x", "y", "vx", "vy")),
            (PhysicsParameters, ("radius", "mass", "gravity", "restitution", "dt")),
            (Box, ("width", "height")),
        ):
            for field in fields:
                for value in (float("nan"), float("inf"), -float("inf")):
                    with self.subTest(field=field, value=value):
                        with self.assertRaises(ValueError):
                            constructor(**{field: value})
        for field in ("radius", "mass", "dt"):
            for value in (0, -1):
                with self.assertRaises(ValueError):
                    PhysicsParameters(**{field: value})
        for options in ({"gravity": -1}, {"restitution": -0.1}, {"restitution": 1.1}):
            with self.assertRaises(ValueError):
                PhysicsParameters(**options)
        for field in ("width", "height"):
            for value in (0, -1):
                with self.assertRaises(ValueError):
                    Box(**{field: value})
        for count in (-1, 1.5, True):
            with self.assertRaises(ValueError):
                CircleState(step_count=count)
        PhysicsParameters(gravity=0, restitution=0)
        PhysicsParameters(restitution=1)

    def test_one_step(self):
        """Check one velocity-first step and the resulting simulation time.

        Returns
        -------
        None
            Results are reported through unittest assertions.

        Raises
        ------
        AssertionError
            If an expected result is not satisfied; unittest records failures.

        Notes
        -----
        Uses dt=0.1 s, vy=3 m/s, and count 7; expects vy=2.019 m/s,
        y=2.2019 m, x=1.15 m, count 8, and time 0.8 s. Prints comparisons;
        uses 1e-12 SI allowances for the measured scalar results.
        See assign3/SPEC.md [EQ-STEP], [EQ-TIME], [EQ-FLIGHT], and [EQ-DRIFT].
        """
        s = CircleState(vy=3.0, step_count=7)
        p = PhysicsParameters(dt=0.1)
        step(s, p)
        # Independently calculated: 3 - .981 = 2.019; 2 + .2019 = 2.2019.
        self.measured("one step vy (m/s)", s.vy, 2.019, 1e-12)
        self.measured("one step y (m)", s.y, 2.2019, 1e-12)
        self.measured("one step x (m)", s.x, 1.15, 1e-12)
        self.assertEqual(s.vx, 1.5)
        self.assertEqual(s.step_count, 8)
        self.measured("one step time (s)", s.time(p), 0.8, 1e-12)

    def test_zero_gravity(self):
        """Check a one-second constant-velocity trajectory.

        Returns
        -------
        None
            Results are reported through unittest assertions.

        Raises
        ------
        AssertionError
            If an expected result is not satisfied; unittest records failures.

        Notes
        -----
        Advances 100 steps at dt=0.01 s with vx=-2 and vy=3 m/s.
        Expects x=-1 m, y=5 m within 1e-10 m and unchanged velocities.
        Prints endpoint comparisons.
        See assign3/SPEC.md [EQ-STEP], [EQ-TIME], [EQ-FLIGHT], and [EQ-DRIFT].
        """
        p = PhysicsParameters(gravity=0, dt=0.01)
        s = CircleState(vx=-2, vy=3)
        for _ in range(100):
            step(s, p)
            self.assertEqual((s.vx, s.vy), (-2, 3))
        self.measured("zero gravity x (m)", s.x, -1, POSITION_TOL)
        self.measured("zero gravity y (m)", s.y, 5, POSITION_TOL)
        self.assertEqual(s.step_count, 100)
        self.assertEqual(s.time(p), 1)

    def test_free_fall_and_refinement(self):
        """Check signed height error and timestep refinement over one second.

        Returns
        -------
        None
            Results are reported through unittest assertions.

        Raises
        ------
        AssertionError
            If an expected result is not satisfied; unittest records failures.

        Notes
        -----
        Uses dt=1/240 and 1/480 s from y=10 m at rest. Checks every-sample
        signed error -g*dt*t/2 with 1e-10 m allowance, final vy=-9.81 m/s,
        matched error difference within 3e-10 m, and endpoint ratio 2 within
        1e-7. Prints measurements; these tolerances bound formula residuals,
        not the distance to the continuous trajectory.
        See assign3/SPEC.md [EQ-STEP], [EQ-TIME], [EQ-FLIGHT], and [EQ-DRIFT].
        """
        histories = []
        for count, expected_y in ((240, 5.0745625), (480, 5.08478125)):
            p = PhysicsParameters(dt=1 / count)
            box = Box(width=100, height=100)
            box.validate_for(p)
            s = CircleState(x=50, y=10, vx=0)
            errors = [0.0]
            max_residual = 0.0
            for n in range(1, count + 1):
                step(s, p)
                self.assertEqual(s.step_count, n)
                t = s.time(p)
                exact = 10 - 0.5 * 9.81 * t * t
                error = s.y - exact
                predicted = -0.5 * 9.81 * p.dt * t
                self.assertAlmostEqual(error, predicted, delta=POSITION_TOL)
                max_residual = max(max_residual, abs(error - predicted))
                self.assertEqual((s.x, s.vx), (50, 0))
                self.assertGreater(s.y, p.radius)
                errors.append(error)
            self.assertEqual(s.time(p), 1.0)
            self.measured(f"dt=1/{count} final y (m)", s.y, expected_y, POSITION_TOL)
            self.measured(f"dt=1/{count} final vy (m/s)", s.vy, -9.81, VELOCITY_TOL)
            self.measured(f"dt=1/{count} signed height error (m)",
                          errors[-1], -0.5 * 9.81 / count, POSITION_TOL)
            print(f"dt=1/{count}: exact final y=5.095 m; "
                  f"max signed-error formula residual={max_residual:.12g} m", flush=True)
            histories.append(errors)
        coarse, fine = histories
        for n in range(1, 241):
            self.assertLess(coarse[n], 0)
            self.assertLess(fine[2 * n], 0)
            self.assertAlmostEqual(abs(coarse[n]), 2 * abs(fine[2 * n]),
                                   delta=3 * POSITION_TOL)
        self.measured("final coarse/fine error ratio", coarse[-1] / fine[-1], 2, 1e-7)


if __name__ == "__main__":
    if sys.version_info[:3] != (3, 12, 10):
        raise SystemExit("Run these checks with Python 3.12.10.")
    print(f"Interpreter: {sys.executable}\nPython: {sys.version}", flush=True)
    unittest.main(verbosity=2)
