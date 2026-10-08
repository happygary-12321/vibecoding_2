# Assignment 3 Part 4 review

Starting commit: `210030d9aff3f996dfd717d6f58cad510953eaff`
(`docs: explain contact decisions and numerical thresholds`), branch `main`.
History and commit contents confirm the reviewed Part 3 comments and artifacts
were committed before editing. All twelve present root Python files had no
changes against this commit. Four pre-existing tracked helper deletions remain.

## Requirement checklist

- [x] Description: README opening describes current 2D gravity/contact physics,
  velocity-first semi-implicit Euler, PyVista and headless validation.
- [x] Installation: Windows CMD root/path, exact intended interpreter version,
  venv creation/activation, simulator and figure requirements, pip consistency
  check, and separately identified report dependencies. Requirements are read
  from the four existing requirements files; none was edited or installed.
- [x] Entry points: GUI and headless commands, both help commands, source-backed
  exit controls, default directory, six output purposes, statuses, and duration
  restrictions. Examples for later runs are not reported as execution.
- [x] CLI: every explicit parser option and automatic help appears in the table,
  with entry point, default, unit, constraints and effect. Python-only physical
  and state parameters are not advertised as CLI flags.
- [x] Conventions/layout: SI, origin, axes, center, gravity sign, coordinate
  pass-through, display units, complete-step order, all 12 modules, and canonical
  assign3 documentation. Deleted helpers are only an audit-time observation.
- [x] Known Issues: all eight requested behaviors are covered and classified;
  other supported scope/validation limits and version-dependent uncertainty are
  distinguished from measured defects.
- [x] Provenance: existing doctest/regression commands, stage verification links,
  before evidence, error log, historical plans/report/provenance links, injected
  bug qualification, and transcript preservation reminder. Assignment 2 evidence
  is not presented as Assignment 3 final verification.
- [x] Narrow SPEC correction: only Section 4's general input-validation paragraph
  changes. It now distinguishes explicit ValueError checks from possible
  OverflowError during math.isfinite of excessively large integers.
- [x] Error record: the previous pending SPEC item is resolved by documentation;
  stale README stage/verification wording and unavailable helper commands are
  recorded as actual corrected documentation issues.
- [x] Scope: README, SPEC, documentation_errors, and this new review only.
  No Python, tests, requirements, historical logs, or baseline evidence edited.

## Supporting implementation and evidence

| README claim | Supporting source |
| --- | --- |
| Shared --restitution=0.8, --dt=1/240, -h/--help; figure-only output-dir=figures, duration=1, bounce-duration=10 | `cli.parse_args`, ArgumentParser construction and add_argument calls; numerical validators `finite_number`, `restitution_value`, `timestep_value` |
| Duration alignment, eight-ulp allowance, 1..1,000,000 steps, doubled fine count and floor limits | `validation.whole_steps`, `validate_experiments`; called by figure parsing and `run_validation` |
| GUI statuses, controls, fixed camera, callback errors | `main.main`, `rendering.run_simulation` (q/Escape bindings, style clearing, camera setup, failure list) |
| Headless outputs/status/error boundaries | `make_figures.main`, `validation.run_validation`, `write_plots`, `regression_checks` |
| SI/default state and gravity sign; updated velocity then contacts | `state.PhysicsParameters/Box/CircleState`, `integration.step/complete_step`, `contacts.resolve_contacts` |
| Persistent rebounds and saved measurement | No cutoff in `resolve_contacts`; saved `evidence/assignment3/before/figures/results.json`, first bouncing run: floor count 1172, final time 10.0, vy 0.01816666666666666; corresponding saved log |
| Energy drift and correction even at e=1 | `validation.free_fall/bouncing` separate expected drift, contact loss, m*g*dy correction; SPEC [EQ-DRIFT], [EQ-ACCOUNTING] |
| No ceiling, side-wall tests above drawing | `contacts.resolve_contacts` lacks y/height wall cutoff or ceiling branch; `rendering.run_simulation` draws finite sides/top guide |
| High trajectories may leave frame | Fixed camera/parallel scale with no actor-following update in `run_simulation`; inference, not a new GUI observation |
| 60-step cap/discard | `rendering.MAX_STEPS_PER_UPDATE`, `FixedStepScheduler.advance` subtracts all available steps and records dropped time |
| Literal radius label | `run_simulation` uses parameters.radius for disk but literal radius 0.2 m text |
| Extreme-integer OverflowError | `state._finite` calls math.isfinite; prior executed example is in `assign3/part2_verification.txt` |
| Old outputs after failure | `run_validation` uses mkdir(exist_ok=True), writes running JSON, does not clear directory, and catches experiment/plot failures |
| Injected defects are separate history | `docs/bug_cases.md` measured Bug A/B records and evidence directories; current step order and inward floor guard are intact |
| Python version and dependencies | All four check script guards require (3,12,10); requirements-figures/rendering/report.txt and aggregate requirements.txt |

Read the actual current source and the accepted SPEC, documentation error log,
Part 3 review, Assignment 2 bug records and provenance. Historical records were
not used to override current implementation.

## Checks performed

- Executed `git status --short`, recent history, branch/HEAD and Part 3 commit
  inspection. Starting unrelated staged additions, untracked files and helper
  deletions were retained.
- Executed an explicit twelve-file `git diff --exit-code HEAD -- ...`: exit 0,
  no source changes. No test execution was needed for these documentation edits.
- Inspected saved before-results/log (read-only), including the reported impact
  count and final velocity. These remain user-run evidence.
- Checked the known interpreter with the exact command:
  `& 'C:\Users\omen16\AppData\Local\Programs\Python\Python312\python.exe' --version`.
  Actual output: `Python 3.12.10`, exit 0. A sandboxed Test-Path was denied;
  the already-known executable was then checked with approved access. No search
  for another interpreter was performed.
- Checked all 13 repository inputs referenced by installation/run/check commands:
  four requirements files, two entry points, three doctest files and four check
  scripts exist. Venv activation/executable paths are products of the documented
  creation command, not a claim that a new venv was created here.
- Checked relative Markdown link destinations from README, SPEC, error record
  and this review. The README's future review link was initially absent until
  this file was created; final checking found all 36 relative destinations exist.
- Reviewed the complete focused documentation diff. SPEC equations, labels,
  criteria and interface tables are unchanged.
- Ran `git diff --check` and the untracked-review whitespace check with
  `git -c core.autocrlf=false diff --no-index --check -- /dev/null assign3/part4_review.md`.
  Tracked diff check: exit 0. Untracked review: exit 1 for new-file differences,
  with no whitespace diagnostics. No runtime pass is implied.
- Compared a SHA256 aggregate of every other existing repository file (excluding
  .git and only the four allowed Part 4 paths), plus the staged-diff hash.
  Matching before/after values:
  - File inventory: `19-8A-AC-52-9F-EB-4F-AF-B0-D1-A6-5E-12-C2-1A-D3-60-77-F0-EC-7F-9B-49-11-3B-29-68-84-36-00-C5-10`.
  - Cached diff: `2bace6e700b8fb35ed0a0d836de1f1b4c825b3c9`.
  This includes byte-preservation of all current Python source and historical
  verification/baseline files. No staging, restoration, commit, or push occurred.

## Not executed / still pending

Installation, venv creation, pip checks, --help, doctests, regression suites and
GUI runs were not executed in Part 4. README commands were checked against
source and file paths. Previously passing doctests are explicitly prior-stage
evidence. Numpydoc lint across every source file and the final before/after
figure comparison remain pending. No figures were generated. The first-impact
criterion remains proposed/unimplemented/unexecuted.

The SPEC OverflowError documentation item is now resolved, while historical
Part 2/3 logs correctly retain their then-pending status. Library-version-specific
GUI concerns remain unverified. No software limitation was fixed.

Preserve the complete Assignment 3 transcript. Part 4 awaits review; no Part 5
work or commit is included.
