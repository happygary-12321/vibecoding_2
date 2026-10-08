"""Check contact directions, record order, endpoints, and bounded motion.

Notes
-----
The script guard requires Python 3.12.10 and prints interpreter details
before invoking unittest. Importing this module does not run its suite.
Tests use the standard library and do not open a GUI.
See assign3/SPEC.md [EQ-NORMAL], [EQ-FLOOR], [EQ-LEFT], and [EQ-RIGHT].
"""

from dataclasses import replace
import sys
import unittest

from contacts import resolve_contacts
from integration import complete_step
from state import Box, CircleState, PhysicsParameters


# A few arithmetic operations at meter scale; far above roundoff, far below
# the 0.05 m corrections and 0.4 m/s restitution changes exercised here.
TOL = 1e-12


class ContactChecks(unittest.TestCase):
    """Check contact directions, record order, endpoints, and bounded motion.

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
    or fixtures and return None. See assign3/SPEC.md [EQ-NORMAL], [EQ-FLOOR],
    [EQ-LEFT], and [EQ-RIGHT].
    """
    def close(self, actual, expected):
        """Assert a scalar contact result within the module's 1e-12 allowance.

        Parameters
        ----------
        actual, expected : float
            Scalars in the same SI unit, usually m or m/s.

        Returns
        -------
        None
            Uses unittest.assertAlmostEqual with delta=TOL.

        Raises
        ------
        AssertionError
            If the scalar comparison fails.
        """
        self.assertAlmostEqual(actual, expected, delta=TOL)

    def test_surfaces_and_directions(self):
        """Check touching and penetrating contacts for every surface.

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
        Exercises inward, separating and zero normal speeds. Checks corrections,
        record velocities/flags, unchanged tangent and count, with 1e-12 SI
        allowances for scalar comparisons. Prints penetrating-case results.
        See assign3/SPEC.md [EQ-NORMAL], [EQ-FLOOR], [EQ-LEFT], and [EQ-RIGHT].
        """
        # Surface, coordinate, velocity, inward-region normal sign, boundary,
        # penetrating coordinate, independently expected signed correction.
        surfaces = (
            ("floor", "y", "vy", 1, 0.2, 0.15, (0, 0.05)),
            ("left", "x", "vx", 1, 0.2, 0.15, (0.05, 0)),
            ("right", "x", "vx", -1, 3.8, 3.85, (-0.05, 0)),
        )
        for name, axis, velocity, sign, boundary, overlap, correction in surfaces:
            for touching in (False, True):
                for before, after, impact in ((-2, 1.6, True), (2, 2, False), (0, 0, False)):
                    with self.subTest(surface=name, touching=touching, normal=before):
                        s = CircleState(vx=0.7, vy=0.7, step_count=5)
                        setattr(s, axis, boundary if touching else overlap)
                        setattr(s, velocity, sign * before)
                        original = replace(s)
                        records = resolve_contacts(s, PhysicsParameters(), Box())
                        self.assertEqual(len(records), 1)
                        record = records[0]
                        self.assertEqual(record.surface, name)
                        self.close(getattr(s, axis), boundary)
                        self.close(getattr(s, velocity), sign * after)
                        self.close(record.normal_velocity_before, before)
                        self.close(record.normal_velocity_after, after)
                        self.assertEqual(record.is_impact, impact)
                        expected_correction = (0, 0) if touching else correction
                        for actual, expected in zip(record.position_correction, expected_correction):
                            self.close(actual, expected)
                        tangent_axis, tangent_velocity = ("x", "vx") if axis == "y" else ("y", "vy")
                        self.assertEqual(getattr(s, tangent_axis), getattr(original, tangent_axis))
                        self.assertEqual(getattr(s, tangent_velocity), getattr(original, tangent_velocity))
                        self.assertEqual(s.step_count, 5)
                        if not touching:
                            print(f"{name}, initial {velocity}={sign * before:+g}: "
                                  f"expected {axis}={boundary}, {velocity}={sign * after:+g}; "
                                  f"measured {axis}={getattr(s, axis):.12g}, "
                                  f"{velocity}={getattr(s, velocity):+.12g}; "
                                  f"impact={record.is_impact}", flush=True)

    def test_no_contact_and_no_ceiling(self):
        """Check that interior states at several heights remain unchanged.

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
        Calls the resolver at y=2, 3, and 10 m with upward motion;
        requires an empty record list and exact preservation of each state.
        See assign3/SPEC.md [EQ-NORMAL], [EQ-FLOOR], [EQ-LEFT], and [EQ-RIGHT].
        """
        for height in (2, 3, 10):
            s = CircleState(y=height, vy=2, step_count=8)
            original = replace(s)
            self.assertEqual(resolve_contacts(s, PhysicsParameters(), Box()), [])
            self.assertEqual(s, original)

    def test_both_corners(self):
        """Check independent floor and wall responses at both lower corners.

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
        Requires floor-first record order, corrected state and signed corrections
        within 1e-12 SI, using inward velocities and default restitution.
        See assign3/SPEC.md [EQ-NORMAL], [EQ-FLOOR], [EQ-LEFT], and [EQ-RIGHT].
        """
        for x, vx, final_x, final_vx, wall, dx in (
            (0.15, -2, 0.2, 1.6, "left", 0.05),
            (3.85, 2, 3.8, -1.6, "right", -0.05),
        ):
            s = CircleState(x=x, y=0.15, vx=vx, vy=-2)
            records = resolve_contacts(s, PhysicsParameters(), Box())
            self.assertEqual([r.surface for r in records], ["floor", wall])
            for actual, expected in zip((s.x, s.y, s.vx, s.vy), (final_x, 0.2, final_vx, 1.6)):
                self.close(actual, expected)
            for record, correction in zip(records, ((0, 0.05), (dx, 0))):
                self.assertTrue(record.is_impact)
                self.close(record.normal_velocity_before, -2)
                self.close(record.normal_velocity_after, 1.6)
                for actual, expected in zip(record.position_correction, correction):
                    self.close(actual, expected)

    def test_restitution_endpoints(self):
        """Check e=0 and e=1 responses at all three surfaces.

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
        For inward normal speed -2 m/s, requires outgoing speeds 0 and 2 m/s
        respectively, one impact record, and scalar comparisons within 1e-12 SI.
        See assign3/SPEC.md [EQ-NORMAL], [EQ-FLOOR], [EQ-LEFT], and [EQ-RIGHT].
        """
        for restitution, speed in ((0, 0), (1, 2)):
            for kwargs, velocity, expected in (
                ({"y": 0.15, "vy": -2}, "vy", speed),
                ({"x": 0.15, "vx": -2}, "vx", speed),
                ({"x": 3.85, "vx": 2}, "vx", -speed),
            ):
                s = CircleState(**kwargs)
                records = resolve_contacts(s, PhysicsParameters(restitution=restitution), Box())
                self.close(getattr(s, velocity), expected)
                self.assertEqual(len(records), 1)
                self.assertTrue(records[0].is_impact)
                self.close(records[0].normal_velocity_before, -2)
                self.close(records[0].normal_velocity_after, speed)

    def test_complete_step_order(self):
        """Check integration before contact correction and one count increment.

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
        Uses g=10 m/s^2 and dt=0.1 s at a lower-left overlap reached by stepping.
        Requires floor/left records, final x=y=0.2 m, vx=vy=0.8 m/s,
        count 8 and time 0.8 s, with 1e-12 SI allowances.
        See assign3/SPEC.md [EQ-NORMAL], [EQ-FLOOR], [EQ-LEFT], and [EQ-RIGHT].
        """
        p = PhysicsParameters(gravity=10, dt=0.1)
        s = CircleState(x=0.25, y=0.25, vx=-1, vy=0, step_count=7)
        records = complete_step(s, p, Box())
        # Before contact: vy=-1, x=y=0.15. Both responses produce +0.8.
        self.assertEqual([r.surface for r in records], ["floor", "left"])
        for actual, expected in zip((s.x, s.y, s.vx, s.vy), (0.2, 0.2, 0.8, 0.8)):
            self.close(actual, expected)
        self.assertEqual(s.step_count, 8)
        self.close(s.time(p), 0.8)
        for record, correction in zip(records, ((0, 0.05), (0.05, 0))):
            self.close(record.normal_velocity_before, -1)
            self.close(record.normal_velocity_after, 0.8)
            self.assertTrue(record.is_impact)
            for actual, expected in zip(record.position_correction, correction):
                self.close(actual, expected)

    def test_default_trajectory(self):
        """Check finite bounded default motion for 2400 complete steps.

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
        Uses dt=1/240 s over 10 s; validates each state, sequential count,
        floor/side bounds, and occurrence of all three impact surfaces.
        Prints the final count/time and surfaces. Does not assert first-impact
        timing, exact settling, or a prescribed number of impacts.
        See assign3/SPEC.md [EQ-NORMAL], [EQ-FLOOR], [EQ-LEFT], and [EQ-RIGHT].
        """
        s, p, box = CircleState(), PhysicsParameters(), Box()
        impacts = set()
        for n in range(1, 2401):  # Ten simulated seconds.
            records = complete_step(s, p, box)
            s.validate()  # Includes finiteness and integer step count.
            self.assertEqual(s.step_count, n)
            self.assertGreaterEqual(s.y, p.radius)
            self.assertGreaterEqual(s.x, p.radius)
            self.assertLessEqual(s.x, box.width - p.radius)
            impacts.update(r.surface for r in records if r.is_impact)
        self.assertEqual(impacts, {"floor", "left", "right"})
        print(f"Default trajectory: measured steps={s.step_count}, time={s.time(p):g} s; "
              f"expected steps=2400, time=10 s; impact surfaces={sorted(impacts)}", flush=True)


if __name__ == "__main__":
    if sys.version_info[:3] != (3, 12, 10):
        raise SystemExit("Run these checks with Python 3.12.10.")
    print(f"Interpreter: {sys.executable}\nPython: {sys.version}", flush=True)
    unittest.main(verbosity=2)
