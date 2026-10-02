"""Deterministic contact checks; no GUI or third-party dependencies."""

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
    def close(self, actual, expected):
        self.assertAlmostEqual(actual, expected, delta=TOL)

    def test_surfaces_and_directions(self):
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
        for height in (2, 3, 10):
            s = CircleState(y=height, vy=2, step_count=8)
            original = replace(s)
            self.assertEqual(resolve_contacts(s, PhysicsParameters(), Box()), [])
            self.assertEqual(s, original)

    def test_both_corners(self):
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
