"""CLI regression checks, including one small headless figure-generation run."""

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
    def invoke(self, entry, *args):
        return subprocess.run(
            [sys.executable, str(ROOT / entry), *args],
            cwd=ROOT, capture_output=True, text=True, check=False,
        )

    def test_defaults(self):
        args = parse_args("CLI check", [])
        self.assertEqual(args.restitution, 0.8)
        self.assertEqual(args.dt, 1.0 / 240.0)

    def test_help(self):
        for entry in ("main.py", "make_figures.py"):
            with self.subTest(entry=entry):
                result = self.invoke(entry, "--help")
                self.assertEqual(result.returncode, 0, result.stderr)
                for expected in ("--restitution", "--dt", "seconds", "default"):
                    self.assertIn(expected, result.stdout)
                self.assertEqual(result.stderr, "")

    def test_main_passes_parameters_without_opening_gui(self):
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
