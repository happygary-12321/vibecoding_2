"""Repeatable Stage 1 checks; no third-party imports or GUI required."""

from pathlib import Path
import subprocess
import sys
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
        for entry in ("main.py", "make_figures.py"):
            for options, restitution, dt in cases:
                with self.subTest(entry=entry, options=options):
                    result = self.invoke(entry, *options)
                    self.assertEqual(result.returncode, 1, result.stderr)
                    self.assertIn("not implemented", result.stderr)
                    self.assertIn(f"restitution={restitution}", result.stderr)
                    self.assertIn(f"dt={dt} s", result.stderr)
                    self.assertEqual(result.stdout, "")

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
