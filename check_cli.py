"""Check CLI parsing, mocked GUI launch, and temporary headless output.

Notes
-----
The script guard requires Python 3.12.10 and prints interpreter details
before invoking unittest. Importing this module does not run its suite.
Some methods spawn subprocesses; test_headless_figures writes temporary
PNGs/JSON. GUI behavior is mocked, not interactively tested.
See assign3/SPEC.md [EQ-STEP] and Section 8.
"""

import json
import builtins
from contextlib import redirect_stderr, redirect_stdout
import io
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from cli import parse_args
import main


ROOT = Path(__file__).resolve().parent


class CliChecks(unittest.TestCase):
    """Check CLI parsing, mocked GUI launch, and temporary headless output.

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
    or fixtures and return None. See assign3/SPEC.md [EQ-STEP] and Section 8.
    """
    def invoke(self, entry, *args):
        """Run an entry script with the current interpreter and capture its output.

        Parameters
        ----------
        entry : str
            Script filename resolved relative to the repository root.
        *args : str
            Additional command-line arguments.

        Returns
        -------
        subprocess.CompletedProcess
            Contains integer returncode and captured text stdout/stderr.

        Raises
        ------
        OSError
            If the subprocess cannot be started.

        Notes
        -----
        Uses the repository root as cwd and check=False, so a nonzero script
        status is returned rather than raised as CalledProcessError. Child
        side effects depend on the requested entry and arguments.
        """
        return subprocess.run(
            [sys.executable, str(ROOT / entry), *args],
            cwd=ROOT, capture_output=True, text=True, check=False,
        )

    def test_defaults(self):
        """Check the default shared CLI values.

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
        Parses an empty argument list and requires restitution 0.8 and
        dt=1/240 s exactly.
        See assign3/SPEC.md [EQ-STEP] and Section 8.
        """
        args = parse_args("CLI check", [])
        self.assertEqual(args.restitution, 0.8)
        self.assertEqual(args.dt, 1.0 / 240.0)

    def test_help(self):
        """Check help status and text for both entry scripts.

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
        Spawns main.py and make_figures.py with --help; captures output,
        requires status 0 and empty stderr, and checks common option text.
        See assign3/SPEC.md [EQ-STEP] and Section 8.
        """
        for entry in ("main.py", "make_figures.py"):
            with self.subTest(entry=entry):
                result = self.invoke(entry, "--help")
                self.assertEqual(result.returncode, 0, result.stderr)
                for expected in ("--restitution", "--dt", "seconds", "default"):
                    self.assertIn(expected, result.stdout)
                self.assertEqual(result.stderr, "")

    def test_main_passes_parameters_without_opening_gui(self):
        """Check parsed parameter forwarding through a mocked renderer.

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
        Temporarily replaces rendering in sys.modules, invokes main with
        four argument sets, and checks one launch call with the expected
        restitution and dt. No native window is opened.
        See assign3/SPEC.md [EQ-STEP] and Section 8.
        """
        cases = (
            ([], 0.8, 1.0 / 240.0),
            (["--restitution=0", "--dt=0.01"], 0.0, 0.01),
            (["--restitution=1", "--dt=1e-3"], 1.0, 0.001),
            (["--restitution=0.25", "--dt=0.02"], 0.25, 0.02),
        )
        for options, restitution, dt in cases:
            with self.subTest(options=options):
                launch = Mock()
                fake = SimpleNamespace(run_simulation=launch, RenderingDependencyError=RuntimeError)
                with patch.dict(sys.modules, {"rendering": fake}):
                    self.assertEqual(main.main(options), 0)
                launch.assert_called_once()
                parameters = launch.call_args.args[0]
                self.assertEqual(parameters.restitution, restitution)
                self.assertEqual(parameters.dt, dt)

    def test_main_help_and_invalid_args_do_not_import_rendering(self):
        """Check that help and invalid options precede rendering imports.

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
        Temporarily guards builtins.__import__, captures stdout/stderr, and
        expects SystemExit 0/2 without importing rendering or pyvista.
        See assign3/SPEC.md [EQ-STEP] and Section 8.
        """
        original_import = builtins.__import__

        def guarded_import(name, *args, **kwargs):
            if name in {"rendering", "pyvista"}:
                raise AssertionError(f"Premature import: {name}")
            return original_import(name, *args, **kwargs)

        for options, expected in ((["--help"], 0), (["--dt=0"], 2), (["--restitution=nan"], 2)):
            with patch("builtins.__import__", side_effect=guarded_import):
                with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                    with self.assertRaises(SystemExit) as caught:
                        main.main(options)
                    self.assertEqual(caught.exception.code, expected)

    def test_main_dependency_message_and_unexpected_errors(self):
        """Check handled dependency failures and propagated programming errors.

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
        Uses a mocked renderer and captured stderr. Requires status 1 for the
        mock dependency error and propagation of an unexpected ValueError.
        See assign3/SPEC.md [EQ-STEP] and Section 8.
        """
        class MissingDependency(RuntimeError):
            pass

        fake = SimpleNamespace(run_simulation=Mock(side_effect=MissingDependency("Install PyVista/VTK")),
                               RenderingDependencyError=MissingDependency)
        output = io.StringIO()
        with patch.dict(sys.modules, {"rendering": fake}), redirect_stderr(output):
            self.assertEqual(main.main([]), 1)
        self.assertIn("Install PyVista/VTK", output.getvalue())
        fake.run_simulation.side_effect = ValueError("unexpected programming error")
        with patch.dict(sys.modules, {"rendering": fake}):
            with self.assertRaisesRegex(ValueError, "unexpected programming error"):
                main.main([])

    def test_figure_options(self):
        """Check figure defaults and rejected durations/timesteps.

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
        Checks default durations/output path and launches invalid-option
        subprocesses. Requires status 2 and relevant error text; no valid
        figure-generation run is requested in this method.
        See assign3/SPEC.md [EQ-STEP] and Section 8.
        """
        args = parse_args("Figures", [], figures=True)
        self.assertEqual((args.duration, args.bounce_duration, args.output_dir), (1, 10, "figures"))
        for option in ("--duration", "--bounce-duration"):
            for value in ("nan", "inf", "-inf", "0", "-1", "abc"):
                with self.subTest(option=option, value=value):
                    result = self.invoke("make_figures.py", f"{option}={value}")
                    self.assertEqual(result.returncode, 2, result.stderr)
                    self.assertIn(option, result.stderr)
        for options, message in (
            (["--dt=0.03"], "whole number"),
            (["--duration=0.101"], "whole number"),
            (["--bounce-duration=0.101"], "whole number"),
            (["--duration=2"], "reaches the floor"),
        ):
            with self.subTest(options=options):
                result = self.invoke("make_figures.py", *options)
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertIn(message, result.stderr)

    def test_headless_figures(self):
        """Check a small figure run and its temporary output artifacts.

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
        Creates a temporary directory, launches make_figures.py with dt=0.02 s,
        both durations 0.2 s and e=0.25, then inspects status/checks, PNG headers,
        backend/import metadata, and regression output. The subprocess performs
        physics checks and writes figures; the directory is removed on exit.
        See assign3/SPEC.md [EQ-STEP] and Section 8.
        """
        with tempfile.TemporaryDirectory() as directory:
            result = self.invoke("make_figures.py", "--output-dir", directory,
                                 "--dt=0.02", "--duration=0.2", "--bounce-duration=0.2",
                                 "--restitution=0.25")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            output = Path(directory)
            report = json.loads((output / "results.json").read_text(encoding="utf-8"))
            self.assertEqual(report["status"], "passed")
            self.assertTrue(all(check["passed"] for check in report["checks"]))
            self.assertEqual(report["parameters"]["restitution"], 0.25)
            self.assertEqual(report["free_fall"][0]["parameters"]["dt"], 0.02)
            self.assertEqual(report["free_fall"][1]["parameters"]["dt"], 0.01)
            self.assertEqual(report["environment"]["matplotlib_backend"].lower(), "agg")
            self.assertEqual(report["environment"]["forbidden_imports"], [])
            self.assertTrue(report["regressions"]["passed"])
            self.assertFalse(report["contact_direction"]["correct_is_impact"])
            self.assertEqual(set(report["figures"]), {
                "free_fall.png", "free_fall_energy.png", "bouncing_energy.png", "contact_direction.png"})
            for name in report["figures"]:
                self.assertTrue((output / name).read_bytes().startswith(b"\x89PNG\r\n\x1a\n"))
            self.assertTrue((output / "regression_checks.txt").is_file())

    def test_invalid_inputs(self):
        """Check invalid numeric arguments on both entry scripts.

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
        Runs subprocesses with malformed, nonfinite, or out-of-range dt/e;
        requires status 2 and parser error text.
        See assign3/SPEC.md [EQ-STEP] and Section 8.
        """
        common = ("nan", "inf", "-inf", "1e309", "abc")
        invalid = {
            "--dt": (*common, "0", "-0", "-0.01"),
            "--restitution": (*common, "-0.01", "1.01"),
        }
        for entry in ("main.py", "make_figures.py"):
            for option, values in invalid.items():
                for value in values:
                    with self.subTest(entry=entry, option=option, value=value):
                        result = self.invoke(entry, f"{option}={value}")
                        self.assertEqual(result.returncode, 2, result.stderr)
                        self.assertIn("error:", result.stderr)
                        self.assertIn(option, result.stderr)

    def test_missing_values(self):
        """Check parser failures when numeric option values are missing.

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
        Runs both entry scripts with bare --dt or --restitution and requires
        status 2 with an expected-one-argument message.
        See assign3/SPEC.md [EQ-STEP] and Section 8.
        """
        for entry in ("main.py", "make_figures.py"):
            for option in ("--dt", "--restitution"):
                with self.subTest(entry=entry, option=option):
                    result = self.invoke(entry, option)
                    self.assertEqual(result.returncode, 2, result.stderr)
                    self.assertIn("expected one argument", result.stderr)


if __name__ == "__main__":
    if sys.version_info[:3] != (3, 12, 10):
        raise SystemExit("Run these checks with Python 3.12.10.")
    print(f"Interpreter: {sys.executable}\nPython: {sys.version}", flush=True)
    unittest.main(verbosity=2)
