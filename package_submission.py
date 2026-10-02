"""Package correct main, report, raw transcript, evidence, and the actual .git directory."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parent
BUGS = {
    "bug_a": ("bug/explicit-euler", "2246cdccb68777de4f97c8800debd2ecff9ab82c", "bug_a_experiment.py"),
    "bug_b": ("bug/unconditional-restitution", "12880a10f2640f74404fca08491608bf94809d1a", "bug_b_experiment.py"),
}


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "submission/HW2_submission.zip")
    args = parser.parse_args()
    if git("branch", "--show-current").decode().strip() != "main" or not (ROOT / ".git").is_dir():
        parser.error("package only the original main worktree with its actual .git directory")
    if git("diff", "71834cd", "--", "state.py", "integration.py", "contacts.py", "rendering.py"):
        parser.error("accepted production physics/rendering differs; review before packaging")
    for branch, commit, helper in BUGS.values():
        if git("rev-parse", branch).decode().strip() != commit:
            parser.error(f"expected local branch {branch} at {commit}")
        git("cat-file", "-e", f"{commit}:{helper}")
    verification = json.loads((ROOT / "evidence/final/summary.json").read_text(encoding="utf-8"))
    transcript = json.loads((ROOT / "docs/transcript/manifest.json").read_text(encoding="utf-8"))
    review = json.loads((ROOT / "docs/report_review.json").read_text(encoding="utf-8"))
    pdf = ROOT / "report.pdf"
    pdf_hash = hashlib.sha256(pdf.read_bytes()).hexdigest()
    if not verification["all_passed"] or not transcript["final_coverage_confirmed_by_user"]:
        parser.error("final checks and final transcript coverage must be confirmed")
    if not all(review[key] for key in ("reflection_reviewed_by_user", "root_cause_wording_reviewed_by_user", "pdf_all_pages_visually_reviewed")):
        parser.error("complete actual report/reflection/root-cause review first")
    if review["reviewed_pdf_sha256"] != pdf_hash:
        parser.error("reviewed PDF hash must match the current report.pdf")
    raw = ROOT / "docs/transcript" / transcript["file"]
    if hashlib.sha256(raw.read_bytes()).hexdigest() != transcript["sha256"]:
        parser.error("transcript snapshot hash mismatch")
    output = args.output.resolve()
    if output.exists():
        parser.error("archive already exists; choose a new --output name")
    output.parent.mkdir(parents=True, exist_ok=True)
    excluded_dirs = {".bug-worktrees", ".venv", "venv", "__pycache__", ".pytest_cache", "tmp", "submission"}
    records = []
    with zipfile.ZipFile(output, "x", compression=zipfile.ZIP_DEFLATED) as archive:
        for directory, folders, files in os.walk(ROOT):
            relative_dir = Path(directory).relative_to(ROOT)
            in_git = relative_dir.parts and relative_dir.parts[0] == ".git"
            if not in_git:
                folders[:] = [folder for folder in folders if folder not in excluded_dirs]
            for name in files:
                path = Path(directory) / name
                if path.resolve() == output:
                    continue
                if not in_git and (name == "test.txt" or name.startswith(("~$", "~WRL")) or path.suffix in {".pyc", ".zip"}):
                    continue
                if path.is_symlink():
                    parser.error(f"review symlink before packaging: {path}")
                relative = path.relative_to(ROOT).as_posix()
                data = path.read_bytes()
                archive.writestr("HW2/" + relative, data)
                records.append(dict(path=relative, sha256=hashlib.sha256(data).hexdigest(), bytes=len(data)))
        # Extra readable helper copies come directly from the exact bug commits.
        # The complete commits and branch refs also remain in the copied .git.
        for name, (branch, commit, helper) in BUGS.items():
            archive.writestr(f"HW2/experiments/{name}/{helper}", git("show", f"{commit}:{helper}"))
        archive.writestr("HW2/submission_manifest.json", json.dumps(dict(
            main_commit=git("rev-parse", "HEAD").decode().strip(), bugs=BUGS,
            pdf_sha256=pdf_hash, files=records), indent=2))
    with zipfile.ZipFile(output) as archive:
        if archive.testzip() is not None or "HW2/.git/HEAD" not in archive.namelist():
            raise RuntimeError("archive verification failed")
    print(f"Created {output}; includes actual .git, both local bug commits, and helper copies.")
    print("No commits, pushes, merges, or git archive operations were performed.")


if __name__ == "__main__":
    main()
