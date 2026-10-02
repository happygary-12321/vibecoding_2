"""Capture final local verification without claiming results before execution."""
from datetime import datetime, timezone
from importlib import metadata
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent


def main():
    if sys.version_info[:3] != (3, 12, 10):
        raise SystemExit("Use Python 3.12.10.")
    branch = subprocess.check_output(["git", "branch", "--show-current"], cwd=ROOT, text=True).strip()
    if branch != "main":
        raise SystemExit("Run final verification from correct main.")
    output = ROOT / "evidence" / "final"
    output.mkdir(parents=True, exist_ok=True)
    commands = [(name, [sys.executable, name + ".py"]) for name in
                ("check_integration", "check_contacts", "check_scheduling", "check_cli")]
    commands += [("make_figures", [sys.executable, "make_figures.py", "--output-dir", "evidence/final/figures"]),
                 ("pip_check", [sys.executable, "-m", "pip", "check"])]
    versions = {}
    for name in ("pyvista", "vtk", "matplotlib", "numpy", "reportlab", "pypdf"):
        try:
            versions[name] = metadata.version(name)
        except metadata.PackageNotFoundError:
            versions[name] = None
    summary = dict(python=sys.version, executable=sys.executable, versions=versions,
                   utc=datetime.now(timezone.utc).isoformat(), branch=branch,
                   commit=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
                   status_before=subprocess.check_output(["git", "status", "--short"], cwd=ROOT, text=True),
                   runs=[], all_passed=False)
    for name, command in commands:
        result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
        (output / f"{name}.txt").write_text("STDOUT:\n" + result.stdout + "\nSTDERR:\n" + result.stderr, encoding="utf-8")
        (output / f"{name}.exit.txt").write_text(str(result.returncode) + "\n", encoding="utf-8")
        summary["runs"].append(dict(name=name, command=command, exit_code=result.returncode))
        print(f"{name}: exit {result.returncode}", flush=True)
    summary["all_passed"] = all(run["exit_code"] == 0 for run in summary["runs"])
    (output / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return 0 if summary["all_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
