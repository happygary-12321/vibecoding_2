"""Synthetic display intervals; standard library only, no GUI/PyVista import."""

import sys
import unittest

from rendering import FixedStepScheduler
from state import Box, CircleState, PhysicsParameters


class SchedulingChecks(unittest.TestCase):
    def scheduler(self, dt=0.01):
        return FixedStepScheduler(CircleState(), PhysicsParameters(dt=dt), Box())

    def test_insufficient_and_fractional_time(self):
        scheduler = self.scheduler(dt=0.1)
        self.assertEqual(scheduler.advance(0), 0)
        self.assertEqual(scheduler.advance(0.04), 0)
        self.assertEqual(scheduler.state.step_count, 0)
        self.assertEqual(scheduler.advance(0.06), 1)
        self.assertEqual(scheduler.state.step_count, 1)
        self.assertAlmostEqual(scheduler.accumulator, 0, delta=1e-12)
        self.assertEqual(scheduler.discarded_time, 0)

    def test_display_interval_independence(self):
        runs = []
        for intervals in ([0.01] * 100, [0.04] * 25, [0.1] * 10):
            scheduler = self.scheduler(dt=1 / 240)
            for elapsed in intervals:
                scheduler.advance(elapsed)
            self.assertEqual(scheduler.state.step_count, 240)
            self.assertEqual(scheduler.discarded_time, 0)
            self.assertAlmostEqual(scheduler.accumulator, 0, delta=1e-12)
            self.assertEqual(scheduler.parameters.dt, 1 / 240)
            runs.append(scheduler.state)
        self.assertEqual(runs[0], runs[1])
        self.assertEqual(runs[0], runs[2])
        print("Display intervals 0.01/0.04/0.1 s: expected 240 steps and identical "
              f"state; measured steps={runs[0].step_count}, states identical.", flush=True)

    def test_cap_discard_and_remainder(self):
        scheduler = self.scheduler()
        self.assertEqual(scheduler.advance(1.2575), 60)
        self.assertEqual(scheduler.state.step_count, 60)
        self.assertEqual(scheduler.discarded_steps, 65)
        self.assertAlmostEqual(scheduler.discarded_time, 0.65, delta=1e-12)
        self.assertAlmostEqual(scheduler.accumulator, 0.0075, delta=1e-12)
        print("Overload: expected steps=60, discarded=0.65 s, remainder=0.0075 s; "
              f"measured steps={scheduler.state.step_count}, "
              f"discarded={scheduler.discarded_time:.12g}, "
              f"remainder={scheduler.accumulator:.12g}", flush=True)
        self.assertEqual(scheduler.advance(0.0025), 1)
        self.assertEqual(scheduler.state.step_count, 61)
        self.assertAlmostEqual(scheduler.accumulator, 0, delta=1e-12)
        self.assertEqual(scheduler.parameters.dt, 0.01)
        self.assertAlmostEqual(scheduler.elapsed_time,
                               scheduler.state.time(scheduler.parameters)
                               + scheduler.discarded_time + scheduler.accumulator, delta=1e-12)

    def test_exact_cap_does_not_discard(self):
        scheduler = self.scheduler()
        self.assertEqual(scheduler.advance(0.6075), 60)
        self.assertEqual(scheduler.discarded_time, 0)
        self.assertAlmostEqual(scheduler.accumulator, 0.0075, delta=1e-12)

    def test_invalid_elapsed(self):
        scheduler = self.scheduler()
        for elapsed in (-1, float("nan"), float("inf")):
            with self.assertRaises(ValueError):
                scheduler.advance(elapsed)
        self.assertEqual(scheduler.state.step_count, 0)
        self.assertEqual(scheduler.accumulator, 0)

    def test_no_pyvista_import(self):
        self.assertFalse(any(name == "pyvista" or name.startswith("pyvista.") for name in sys.modules))


if __name__ == "__main__":
    if sys.version_info[:3] != (3, 12, 10):
        raise SystemExit("Run these checks with Python 3.12.10.")
    print(f"Interpreter: {sys.executable}\nPython: {sys.version}", flush=True)
    unittest.main(verbosity=2)
