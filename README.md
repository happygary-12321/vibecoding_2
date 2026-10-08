# Circle simulator

This simulator moves a 2D circle under constant gravity inside an open box, using velocity-first semi-implicit Euler integration and radius-based floor and side-wall collisions with configurable restitution. A native PyVista window displays the motion in real time; a separate headless entry point produces numerical validation, energy accounting, and figures.

## Installation on Windows

Use **Python 3.12.10**. All four regression scripts explicitly require that exact version; no other Python version is claimed verified. From the repository root, these **CMD** commands use the interpreter already verified on this machine. On another machine, replace the quoted interpreter path with the path to its Python 3.12.10 installation.

```bat
cd /d D:\CodexCLI\vibecoding\HW2
"C:\Users\omen16\AppData\Local\Programs\Python\Python312\python.exe" --version
"C:\Users\omen16\AppData\Local\Programs\Python\Python312\python.exe" -m venv .venv
call .venv\Scripts\activate.bat
python --version
python -m pip install -r requirements-figures.txt -r requirements-rendering.txt
python -m pip check
python -m pip show matplotlib pyvista vtk
```

Use an existing suitable environment instead of recreating it. After activation, the commands below use its Python; use `.venv\Scripts\python.exe` explicitly if needed. Run `deactivate` to leave it.

[Figure requirements](requirements-figures.txt) declare Matplotlib. [Rendering requirements](requirements-rendering.txt) declare `pyvista>=0.46.3`; pip resolves its dependencies, including VTK. Physics and the integration/contact/scheduler checks use the standard library; the CLI check also needs the plotting dependencies. These files do not pin a complete environment, so retain actual installed versions with verification results. The renderer prints Python/PyVista/VTK versions; figure results record Python and plotting-package versions.

[Report requirements](requirements-report.txt) contain `reportlab` and `pypdf`, which are not needed to run the simulator or figures. If working on report tooling, install them separately:

```bat
python -m pip install -r requirements-report.txt
python -m pip check
```

The aggregate [requirements.txt](requirements.txt) includes all three lists. Installation commands are instructions, not evidence that packages were installed during this documentation stage.

## Run the simulator or generate figures

```bat
python main.py --help
python make_figures.py --help
python main.py
python make_figures.py
```

**Interactive:** `python main.py` opens the native PyVista window and runs until it closes. Press **q** or **Escape**, or use the window close button. The code clears the interaction style and default key callbacks, then binds the two exit keys; it provides no application camera controls. The parallel camera has fixed framing. Startup prints versions/settings; shutdown prints simulated steps/time and discarded backlog. Historical user feedback that the GUI worked is recorded in the prior documentation; no new GUI check was performed for Part 4.

**Headless:** `python make_figures.py` runs integration/contact regressions, coarse/fine free fall, selected-restitution and elastic bouncing, and the contact-direction diagnostic. It uses Matplotlib Agg without opening PyVista. By default it creates or reuses `figures/` relative to the current directory. Existing same-named files are overwritten. For a separate run, select a fresh directory; never target the saved `evidence/assignment3/before/` baseline.

```bat
python main.py --restitution 0.5 --dt 0.0020833333333333333
python make_figures.py --output-dir assign3/figures_after --restitution 0.8
```

The second example selects a separate directory. Part 5 verification instead ran the required literal `python make_figures.py` command with its default `figures/` output, then preserved the six resulting files under `assign3/after/`.

| Output within the selected directory | Purpose |
| --- | --- |
| `free_fall.png` | Coarse/fine heights and signed errors against analytical references. |
| `free_fall_energy.png` | Measured and predicted contact-free integration energy drift. |
| `bouncing_energy.png` | Impact markers and integration/restitution/position-correction energy contributions for selected e and e=1. |
| `contact_direction.png` | Upward-overlap response from the real resolver versus an isolated illustrative faulty rule; the diagnostic uses e=0.8 independently of the CLI selection. |
| `results.json` | Status, environment, parameters, durations, checks/tolerances, numerical traces, contact records/counts, and figure list. |
| `regression_checks.txt` | Captured integration/contact regression output. It does not represent the CLI or scheduler suites. |

Help exits with status **0**; argument/range/duration errors exit with **2** through argparse. Normal GUI completion returns **0**; missing PyVista/VTK handled by `main.main` prints an installation message and returns **1**. Other unexpected GUI errors propagate, including saved callback exceptions after the event loop ends.

Figure generation returns **0** for a passed report and **1** for a failed report or caught `OSError`. Experiment/plotting exceptions inside the validator's guarded block become failed reports with tracebacks. Setup and final serialization errors outside that block can propagate. Inspect the current JSON status and figure list, not just the presence of PNGs.

## Command-line options

“Both” means `main.py` and `make_figures.py`. Numeric arguments accept decimal/scientific notation; the expression `1/240` is not evaluated. Initial state, gravity, mass, radius, and box dimensions are Python-only configuration, not CLI options.

| Entry point | Option | Default | Units | Accepted values / constraints | Effect |
| --- | --- | --- | --- | --- | --- |
| Both | `-h`, `--help` | Not requested | None | No value | Print help and exit 0. |
| Both | `--restitution` | 0.8 | Dimensionless | Finite float in [0, 1], endpoints included | Set inward-contact restitution. |
| Both | `--dt` | 1/240 (about 0.004166666666666667) | s | Finite float >0; figure constraints below also apply | Set fixed physics step; free-fall fine run uses dt/2. |
| Figures only | `--output-dir` | figures | Path | String; no parser writability check; directory must be creatable/writable at execution | Select output directory. |
| Figures only | `--duration` | 1.0 | s | Finite, positive, aligned duration; free fall must remain above floor | Set coarse and fine free-fall interval. |
| Figures only | `--bounce-duration` | 10.0 | s | Finite, positive, aligned duration | Set each bouncing interval, including e=1 diagnostic. |

For figures, each duration/timestep quotient must be finite and within eight ulps of an integer, with **1 to 1,000,000 steps per run**, including the dt/2 fine run. Fine free fall must have exactly twice the coarse step count. The free-fall duration must precede continuous floor contact and leave the predicted coarse discrete endpoint strictly above radius 0.2 m (from y=10 m at rest, g=9.81 m/s²). The default 1 s satisfies these checks. The parser rejects invalid experiments and may suggest an aligned duration; it never silently adjusts dt. Sources: `cli.parse_args` and `validation.validate_experiments/whole_steps`.

## Conventions and source layout

Physics uses SI units: meters, seconds, kilograms, m/s and m/s²; restitution and step counts are dimensionless. The origin is the floor's left end, +x points right, +y up, and state coordinates locate the circle center. Gravity is stored as a nonnegative magnitude and subtracted from vy. Defaults are radius 0.2 m, mass 1 kg, g=9.81 m/s², box 4 by 3 m, center (1, 2) m, and velocity (1.5, 0) m/s.

Each complete step validates geometry, updates vy, then x and y using the updated velocity, increments the step count, and resolves floor/left/right contacts in that order. Edge tests include exact touch. Penetration correction does not require inward motion; restitution does. Direct contact resolution does not advance time. Keep dt fixed for a trajectory because time is computed as step_count × dt.

Rendering passes (x, y, 0) and the physical radius directly into scene coordinates without application-level meters-to-pixels scaling. Window sizes and line widths are display pixels; fonts, tessellation, and camera framing are display settings. The requested 16 ms timer is not the physics timestep: elapsed seconds feed a fixed-step scheduler.

| Root module | Responsibility |
| --- | --- |
| [main.py](main.py) | GUI entry point, parameter construction, handled dependency failure status. |
| [make_figures.py](make_figures.py) | Headless entry point, validation summaries and exit status. |
| [cli.py](cli.py) | Shared parser and figure-only options/duration validation. |
| [state.py](state.py) | Mutable circle state, frozen physics/box dataclasses, explicit validation, simulation time. |
| [integration.py](integration.py) | Contact-free semi-implicit Euler and the complete integration/contact step. |
| [contacts.py](contacts.py) | Floor/wall correction and inward-velocity response; immutable contact records. |
| [rendering.py](rendering.py) | Fixed-step scheduler, native PyVista scene, camera, timer and GUI lifecycle. |
| [validation.py](validation.py) | Headless numerical experiments, energy accounting, captured regressions, JSON and PNG output. |
| [check_cli.py](check_cli.py) | Parser/status and mocked GUI-dispatch regressions; temporary headless figure smoke test. |
| [check_integration.py](check_integration.py) | State/default/range, step order, free-fall and timestep-refinement regressions. |
| [check_contacts.py](check_contacts.py) | Contact direction, touching, corners, restitution endpoints, complete-step and bounded-trajectory checks. |
| [check_scheduling.py](check_scheduling.py) | Synthetic elapsed-time, fractional remainder and backlog-discard checks without a GUI. |

[assign3/SPEC.md](assign3/SPEC.md) holds stable equation labels, detailed conventions, interfaces and validation criteria. Other `assign3/` files record documentation reviews, errors and verification. Duplicate submission folders and intentional-bug worktrees are not simulator modules.

**Audit-time working-tree status:** the tracked `build_report.py`, `final_verify.py`, `package_submission.py`, and `preserve_transcript.py` helpers are locally deleted. They are not available commands in this checkout. This is a working-tree observation, not a permanent module-layout decision.

## Known Issues and limitations

- **Numerical contact limitation:** there is no resting-speed cutoff or continuous impact-time resolution. Small floor rebounds persist rather than reaching exact rest. The saved user-run [before results](assign3/before/figures/results.json) record 1,172 floor impacts and vy≈+0.0181667 m/s at 10 s for defaults; the [saved log](assign3/before/make_figures.log) records the impact count. This was not a new Part 4 run. The fixed timestep does not resolve the finite-time accumulation of ideal inelastic bounces described in SPEC.
- **Numerical energy limitation:** semi-implicit Euler introduces contact-free energy drift, and vertical position projection changes potential energy. Even e=1 removes only restitution loss, not those effects. Small accounting residuals do not mean an equally small error against the continuous trajectory.
- **Intentional scope and geometry limitation:** there is no ceiling, friction, rotation, or circle-circle collision. Side-wall tests continue above the drawn wall height; the top dashed line is only a guide.
- **Display limitation:** the fixed camera does not follow high trajectories, so they may leave the visible frame while physics continues. This consequence follows from the framing and absence of a height bound; no new off-screen GUI experiment was performed.
- **Scheduling policy:** each update executes at most 60 steps. Additional whole-step backlog is discarded permanently, retaining only the fraction. Overload can make simulated time lag wall time; dt is not enlarged.
- **Display defect for Python customization:** the scene text literally says radius 0.2 m even when `run_simulation` receives a different valid radius. The CLI does not expose radius.
- **Validation limitation:** excessively large Python integers can propagate `OverflowError` from `math.isfinite` in `state._finite`. Explicit type/finiteness/range checks raise `ValueError`; they are not a universal exception guarantee. Low-level mutation/integration also does not validate every subsequent arithmetic result.
- **Output lifecycle limitation:** failed reruns can leave old PNGs or other previous outputs because the directory is not cleared first. Use a fresh directory and inspect current status/figure metadata.
- **Unverified concern:** detailed PyVista/VTK interaction and cleanup behavior across dependency versions has not been rechecked during documentation. The minimum requirement is not a guarantee that every later version was tested.

The [Assignment 2 bug case studies](docs/bug_cases.md) intentionally changed Euler order and removed the floor velocity-direction guard in separate local branches. Their local `evidence/bug_a/` and `evidence/bug_b/` saved results are historical injected-defect evidence, not unresolved defects in the current simulator. Current integration remains velocity-first, and upward floor overlap preserves upward velocity.

## Verification and provenance

After activating Python 3.12.10, run the existing checks from the root:

```bat
python -B -m doctest -v state.py integration.py contacts.py
python -B check_integration.py
python -B check_contacts.py
python -B check_scheduling.py
python -B check_cli.py
python -m pip check
```

The CLI suite generates a short headless run in a temporary directory; these commands are not all read-only. It does not launch a GUI. Numerical checks distinguish signed integration error from floating-point residuals; detailed tolerances and the still-proposed first-impact criterion are in SPEC. That proposed criterion remains unimplemented and unexecuted.

[Part 2 verification](assign3/part2_verification.txt) and [Part 3 verification](assign3/part3_verification.txt) record actual checks. Part 3 reports 19 physics doctest examples passing on Python 3.12.10, all 12 full AST comparisons retaining docstrings, and non-comment token comparisons. These are prior-stage results, not tests rerun for this README. [Part 3 review](assign3/part3_review.md), [Part 4 review](assign3/part4_review.md), and [documentation errors](assign3/documentation_errors.md) explain changes and qualifications.

**Part 5 behavior verification passed; raw documentation lint retains nine evidenced checker limitations.** The [final audit](assign3/part5_summary.md) and [complete logs](assign3/verification/) record Python 3.12.10 and distinguish the **earlier** 19-example physics run, four regression suites and `pip check` from the **final revised documentation** run of 326 statements across 75 objects. Executable ASTs for all 12 modules remain equal to the Assignment 3 starting commit. The literal figure command was run once more against the accepted final source and passed all 26 numerical checks and 11 embedded regressions. [Final source hashes](assign3/verification/final_source_hashes.json) identify the exact 12 working-tree files used; [final command and log](assign3/verification/final_make_figures.command.txt) are saved separately from earlier verification. All four PNGs and `results.json` are byte-identical to the saved baseline; [comparison results](assign3/comparison_results.json) include hashes and pixel checks. The regression text differs in documentation-derived descriptions and elapsed time.

Numpydoc 1.11.0 was installed without changing any existing package version. Initial/final diagnostics and per-file exits are retained. The literal wildcard invocation fails on this Windows path; explicit filenames cover all 12 sources. Genuine capitalization/missing-local-docstring issues were corrected. After review, all ES01, SA01, and EX01 findings were corrected with useful summaries, genuine cross-references, and examples. All 326 runnable example statements across 75 objects passed, including examples in local helper docstrings; the native GUI example is explicitly manual and was not executed. The final unsuppressed lint exits **1** with exactly **nine PR02 false positives** for valid inherited/dataclass constructor parameters. Their accurate Parameters sections and runtime-signature evidence are preserved; this is not a zero-exit lint claim. See [revision results](assign3/verification/lint_revision_summary.json) and [raw diagnostics](assign3/verification/lint_reviewed_all.log). No GUI session was run in Part 5.

The byte-preserved submission copy of the [Assignment 3 before evidence](assign3/before/) identifies starting commit `604a32d3d9c8d400a2ecedb7d35f36eee29563fb` and contains saved user-local execution results. Its original location remains `evidence/assignment3/before/`, unchanged. The copy's hashes match every original file. Its exact shell command was not recorded; do not reconstruct it as established fact. Local `evidence/final/` is historical Assignment 2 evidence, not Assignment 3 final verification; its pre-existing staged additions are outside the proposed Part 5 commit.

Historical materials remain available: [original plan](docs/original_plan.md), [change log](docs/change_log.md), [provenance](docs/provenance.md), [report source](docs/report.md), [report PDF](report.pdf), and [report review record](docs/report_review.json). Their stage-specific claims and outstanding review status should be read in that historical context; the current implementation is authoritative.

The [Assignment 3 transcript manifest](assign3/transcript/manifest.json) identifies a byte-preserved raw session snapshot, its hash and coverage. Session metadata records `codex-tui` 0.160.0, source VS Code, provider OpenAI; recorded turn model identifiers are `gpt-6-astra`. These are metadata observations, not a name inferred from the harness. The [historical transcript index](docs/transcript/README.md) refers to Assignment 2 and is separate.

**Submission remains under review:** new `assign3/` evidence is not yet staged/committed, lint remains nonzero, and the active transcript must be refreshed after final review. [Final transcript refresh procedure](assign3/transcript/REFRESH.md) and [remaining items](assign3/part5_summary.md) account for the four local helper deletions and unrelated staged evidence. The tested working tree is not a verified fresh clone. Preserve the complete Assignment 3 transcript.
