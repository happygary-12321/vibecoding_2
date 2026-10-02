"""CLI regression checks, including one small headless figure-generation run."""

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from cli import parse_args


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

    def test_valid_inputs_reach_unimplemented_path(self):
        cases = (
            ([], 0.8, 1.0 / 240.0),
            (["--restitution=0", "--dt=0.01"], 0.0, 0.01),
            (["--restitution=1", "--dt=1e-3"], 1.0, 0.001),
            (["--restitution=0.25", "--dt=0.02"], 0.25, 0.02),
        )
        for entry in ("main.py",):
            for options, restitution, dt in cases:
                with self.subTest(entry=entry, options=options):
                    result = self.invoke(entry, *options)
                    self.assertEqual(result.returncode, 1, result.stderr)
                    self.assertIn("not implemented", result.stderr)
                    self.assertIn(f"restitution={restitution}", result.stderr)
                    self.assertIn(f"dt={dt} s", result.stderr)
                    self.assertEqual(result.stdout, "")

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
                        self.assertNotIn("not implemented (Stage", result.stderr)

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
