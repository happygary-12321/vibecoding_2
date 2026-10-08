"""Check fixed-step scheduling with synthetic elapsed intervals.

Notes
-----
The script guard requires Python 3.12.10 and prints interpreter details
before invoking unittest. Importing this module does not run its suite.
Tests use the standard library and do not open a GUI.
See assign3/SPEC.md [EQ-STEP] and [EQ-TIME].
"""

import sys
import unittest

from rendering import FixedStepScheduler
from state import Box, CircleState, PhysicsParameters


class SchedulingChecks(unittest.TestCase):
    """Check fixed-step scheduling with synthetic elapsed intervals.

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
    or fixtures and return None. See assign3/SPEC.md [EQ-STEP] and [EQ-TIME].
    """
    def scheduler(self, dt=0.01):
        """Construct a scheduler with default state and box for a test.

        Parameters
        ----------
        dt : float, optional
            Positive finite fixed timestep in s; default 0.01.

        Returns
        -------
        FixedStepScheduler
            New mutable scheduler with zero bookkeeping counters.

        Raises
        ------
        ValueError
            If PhysicsParameters rejects dt.

        Notes
        -----
        Creates no GUI or PyVista resources. See assign3/SPEC.md [EQ-TIME].
        """
        return FixedStepScheduler(CircleState(), PhysicsParameters(dt=dt), Box())

    def test_insufficient_and_fractional_time(self):
        """Check accumulation of intervals shorter than one timestep.

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
        Uses dt=0.1 s and elapsed intervals 0, 0.04, 0.06 s; expects one step,
        no discarded time, and final remainder within 1e-12 s of zero.
        See assign3/SPEC.md [EQ-STEP] and [EQ-TIME].
        """
        scheduler = self.scheduler(dt=0.1)
        self.assertEqual(scheduler.advance(0), 0)
        self.assertEqual(scheduler.advance(0.04), 0)
        self.assertEqual(scheduler.state.step_count, 0)
        self.assertEqual(scheduler.advance(0.06), 1)
        self.assertEqual(scheduler.state.step_count, 1)
        self.assertAlmostEqual(scheduler.accumulator, 0, delta=1e-12)
        self.assertEqual(scheduler.discarded_time, 0)

    def test_display_interval_independence(self):
        """Check identical states for three one-second display schedules.

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
        Uses dt=1/240 s and intervals 0.01, 0.04, or 0.1 s. Requires exact
        state equality and 240 steps without discard; remainder tolerance is
        1e-12 s. Prints the comparison.
        See assign3/SPEC.md [EQ-STEP] and [EQ-TIME].
        """
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
        """Check the 60-step cap and discarded whole-step backlog.

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
        At dt=0.01 s, supplies 1.2575 s: expects 60 steps, 65 discarded steps,
        0.65 s discarded, and 0.0075 s retained. Then supplies 0.0025 s
        and expects one step. Time allowances are 1e-12 s; prints counters.
        See assign3/SPEC.md [EQ-STEP] and [EQ-TIME].
        """
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
        """Check that exactly 60 available steps leave no discarded time.

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
        Uses dt=0.01 s and elapsed=0.6075 s, retaining 0.0075 s within
        1e-12 s while executing exactly 60 steps.
        See assign3/SPEC.md [EQ-STEP] and [EQ-TIME].
        """
        scheduler = self.scheduler()
        self.assertEqual(scheduler.advance(0.6075), 60)
        self.assertEqual(scheduler.discarded_time, 0)
        self.assertAlmostEqual(scheduler.accumulator, 0.0075, delta=1e-12)

    def test_invalid_elapsed(self):
        """Check rejection of negative and nonfinite elapsed intervals.

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
        Requires ValueError for -1, NaN and infinity and no state/count or
        accumulator advancement in these cases.
        See assign3/SPEC.md [EQ-STEP] and [EQ-TIME].
        """
        scheduler = self.scheduler()
        for elapsed in (-1, float("nan"), float("inf")):
            with self.assertRaises(ValueError):
                scheduler.advance(elapsed)
        self.assertEqual(scheduler.state.step_count, 0)
        self.assertEqual(scheduler.accumulator, 0)

    def test_no_pyvista_import(self):
        """Check that the current process has not loaded PyVista.

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
        Inspects sys.modules for pyvista and submodules. Does not launch a
        renderer; an unrelated earlier PyVista import would fail this assertion.
        See assign3/SPEC.md [EQ-STEP] and [EQ-TIME].
        """
        self.assertFalse(any(name == "pyvista" or name.startswith("pyvista.") for name in sys.modules))


if __name__ == "__main__":
    if sys.version_info[:3] != (3, 12, 10):
        raise SystemExit("Run these checks with Python 3.12.10.")
    print(f"Interpreter: {sys.executable}\nPython: {sys.version}", flush=True)
    unittest.main(verbosity=2)
