# vibecoding_2

Circle simulation assignment. Stage 5 adds native PyVista real-time rendering.
Physics includes SI-unit state, semi-implicit Euler, and floor/side-wall contacts.
Headless validation, energy accounting, PNG figures, and JSON results remain
available independently. The accepted baseline is `38cd01e`; Stage 5 automated
reruns and interactive GUI verification are pending local execution.

## Python and dependencies

Use **Python 3.12.10** consistently. Check `python --version` before running
commands; the unqualified `py` launcher may select a different version.
Physics, contact, integration, and scheduling checks need only the standard library.
Figure generation and its CLI smoke test require Matplotlib and its dependencies.
Install rendering dependencies in the same Python 3.12.10 environment used for
the accepted figures. The following also ensures figure dependencies are present:

```text
python --version
python -m pip install -r requirements-figures.txt
python -m pip install -r requirements-rendering.txt
python -m pip check
python -m pip show pyvista vtk
```

No packages were installed in the agent session: Python execution is unavailable.
Successful generation records actual Python, executable, Matplotlib, NumPy, and
plotting dependency versions in `results.json`; no versions are guessed.
The renderer prints actual Python, PyVista, and VTK versions at startup. Preserve
that output with the GUI observations before recording verified versions.
`pyvista>=0.46.3` is an API minimum checked against upstream source, not a claim
that this version is installed or locally tested. No Qt dependency is required.

For later stages, create an environment using the verified interpreter:

```text
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Dependency versions will be recorded after actual installation and verification.

## Commands available now

```text
python main.py --help
python make_figures.py --help
python main.py --restitution 0.8 --dt 0.004166666666666667
python make_figures.py --restitution 0.8 --dt 0.004166666666666667
python check_cli.py
python check_integration.py
python check_contacts.py
python check_scheduling.py
```

Both entry points accept `--restitution` (default 0.8, finite and in [0, 1])
and `--dt` (seconds, default 1/240, finite and greater than zero). Supply a
decimal or scientific-notation number, not a literal expression such as `1/240`.
Invalid inputs exit with status 2. Help exits with status 0. `main.py` validates
arguments before importing rendering, then passes the selected restitution and
dt into `PhysicsParameters` and opens the native window. Missing PyVista/VTK
produces an installation message and status 1. Unexpected errors retain their
tracebacks. Normal GUI shutdown returns status 0. `make_figures.py` exits with status 0 only after
all required numerical checks and figure writes succeed; failures exit nonzero.

`check_cli.py` requires Python 3.12.10 and checks both help paths, parsed defaults,
custom values, restitution endpoints, invalid numbers, missing values, duration
constraints, mocked `main.py` parameter forwarding/error handling, and a small headless figure run in
a temporary output directory. That run also executes the physics regression suites.
No automated CLI check opens an interactive GUI. Help and invalid-option tests
also guard against importing rendering before argument validation.

`check_integration.py` also requires Python 3.12.10. It prints expected and
measured values for one-step motion, zero gravity, and one-second free fall at
1/240 s and 1/480 s. It checks the signed semi-implicit Euler height error at
every sample and compares coarse samples with every second fine sample.
Expected final heights are 5.0745625 m and 5.08478125 m, respectively; both final
vertical velocities are -9.81 m/s. These are references, not claimed test results.
Stage 2 was accepted and committed by the user at `1c9fdce`.

Checks use absolute tolerances of 1e-12 for single-step values and 1e-10 m or
m/s for trajectories of at most 480 steps, allowing roundoff while remaining far
below the approximately 0.01 m discretization error. The refinement difference
allows 3e-10 m (one coarse plus twice one fine tolerance); its endpoint ratio
allows 1e-7, conservatively accounting for division by a roughly 0.01 m error.

## Module boundaries

Present: `cli.py` owns shared parsing; `main.py` and `make_figures.py` are entry
points. `check_cli.py` provides ongoing CLI regression checks.

`state.py` defines mutable `CircleState` and frozen `PhysicsParameters` and
`Box` dataclasses. Construction validates finite values and physical ranges;
`state.validate()` can recheck manually edited state. Positions may penetrate
surfaces or exceed the displayed height. `box.validate_for(parameters)` checks
both box dimensions against the selected diameter. `state.time(parameters)`
returns `step_count * dt`; keep dt fixed throughout each trajectory.

`integration.step(state, parameters)` mutates state in place: update vy with
gravity, update x and y using the new velocity, then increment the integer step
count once. vx is unchanged. This contact-free function assumes valid input
state and does not use box geometry or enforce boundaries. `check_integration.py`
is the Stage 2 verification command. No third-party dependencies are required.

`contacts.resolve_contacts(state, parameters, box)` corrects floor, left-wall,
and right-wall contacts in that order, reflecting only inward normal velocity.
Outward and zero normal velocity are preserved, as is tangential velocity.
Direct resolution does not advance time. Both floor-wall corner components are
resolved independently. There is no ceiling, friction, rotation, continuous
collision detection, or resting-contact threshold.

`integration.complete_step(state, parameters, box)` calls the existing contact-free
`step` once, then resolves contacts and returns records. It increments the count
exactly once through `step`. Keep using `step` for contact-free validation.

Each `ContactRecord` contains `surface` (`floor`, `left`, or `right`), signed
`position_correction` `(dx, dy)` in meters, and normal velocities before and after
response in m/s. Normals point into the allowed region: +y, +x, and -x respectively.
Thus positive normal velocity means moving away, including at the right wall.
`is_impact` is true only when normal velocity actually changes. Touching or
position-only correction still produces a record but is not an impact.

`check_contacts.py` uses Python 3.12.10 and the standard library. It checks all
three surfaces, inward/outward/zero velocities, exact touching, no contact,
tangential preservation, corners, restitution endpoints, records, step order,
and a 2400-step default trajectory. Direct checks use absolute tolerance 1e-12
in the relevant SI unit: enough for roundoff over a few operations, much smaller
than the response being tested. Representative expected/measured values are
printed, including the upward-moving floor overlap (expected y=0.2, vy=+2).
Stage 3 was accepted at `a5f5654`; Stage 4 and its dependency update were accepted
through `38cd01e`. Stage 5 regression reruns remain pending.

`rendering.py` alone owns PyVista, camera, meshes,
colors, display settings, and fixed-step real-time scheduling. `validation.py`
now provides deterministic headless checks and plots. No ceiling collision.
Unimplemented modules are not represented by empty placeholder files.

## Headless numerical validation (Stage 4)

```text
python check_contacts.py
python check_integration.py
python check_cli.py
python make_figures.py --output-dir figures
python make_figures.py --restitution 0.6 --dt 0.0020833333333333333 --output-dir figures_fine
```

`--duration` sets free-fall duration (default 1 second); `--bounce-duration` sets
each bouncing run's duration (default 10 seconds). Both must be positive, finite,
and aligned to whole timesteps. Alignment allows eight ulps of quotient roundoff;
errors suggest an aligned duration. dt is never silently adjusted. The free-fall
fine run uses dt/2 and must have exactly twice the coarse step count. A requested
duration is rejected if the predicted coarse free-fall endpoint reaches the floor.
Experiments are limited to one million steps per run to bound trace size and work;
larger requests receive an error suggesting a shorter duration or larger dt.

Free fall starts at rest at (50, 10) m in a 100-by-100 m box. Every sample,
including time zero, is saved. The integrator produces the trajectories; analytical
formulas are used only as references. Matching samples check the signed error
`-g*dt*t/2` and that halving dt halves it. Both per-step and cumulative contact-free
energy drift are checked. Defaults expect heights 5.0745625 m and 5.08478125 m
against 5.095 m analytical height, and final vy=-9.81 m/s. Expected energy drifts
are -0.200491875 J and -0.1002459375 J. These are references, not measured results.

Bouncing uses `complete_step` for both the selected restitution and an additional
e=1 diagnostic. Recorded normal velocities give measured contact kinetic-energy
changes; signed position corrections give `m*g*dy`. Subtracting those from the
post-step energy reconstructs pre-contact energy without duplicating integration.
Checks compare integration drift with `-m*g*g*dt*dt/2`, inward-contact restitution
loss with `-m*(1-e*e)*vn_before*vn_before/2`, and total/cumulative accounting.
Correction energy is a numerical artifact, not physical restitution loss. Even
the elastic discrete simulation can drift; no exact-conservation claim is made.

Tolerances use `max(base, 8*machine_epsilon*step_count*max(1, scale))`, with bases
1e-10 m or m/s and 1e-9 J; scale is the experiment's height, speed, or energy.
The factor-eight budget allows accumulated arithmetic roundoff, not truncation
error. Matching-error tolerance is coarse tolerance plus twice fine tolerance.
Direct contact checks retain 1e-12 SI. Actual tolerances and residuals are saved.

Outputs (existing files with these names are replaced on rerun):

| File | Caption / interpretation |
|---|---|
| `free_fall.png` | Height and signed error versus time, dt and dt/2, with analytical predictions. Measured/predicted error lines should overlap. |
| `free_fall_energy.png` | Measured and predicted contact-free energy drift; finer steps reduce drift. |
| `bouncing_energy.png` | Selected e and elastic runs; actual floor/left/right impacts marked above, cumulative integration/restitution/correction contributions below. |
| `contact_direction.png` | Upward-moving floor overlap: real resolver preserves +2 m/s; illustrative faulty rule gives -1.6 m/s. Both correct y to 0.2 m. |
| `results.json` | Parameters, durations, versions, check outcomes/tolerances, expected/measured values, complete numerical traces, residuals, contact records, and impact counts. |
| `regression_checks.txt` | Actual integration/contact regression output, including failures if any. |

The direction comparison always uses e=0.8, independently of the CLI choice.
It calls the real resolver for the correct response and checks y=0.2, vy=+2,
and no impact. The faulty comparison is isolated in validation code and is
explicitly **not evidence of an injected production-code defect**.

Matplotlib uses Agg, selected before importing pyplot. The validation path never
imports PyVista or rendering, and checks loaded modules for those imports.
Failed numerical checks retain traces and diagnostic figures when possible;
unexpected errors save a traceback in `results.json` and cause a nonzero exit.
Check `status` and the figure list in the current JSON: old PNG files can remain
after a failed rerun. Unwritable output directories are reported to stderr.
Stage 4 was accepted by the user. The Stage 5 rerun has not been executed in the
agent session; no new plot inspection or runtime results are claimed.

## Real-time rendering (Stage 5)

```text
python main.py
python main.py --restitution 0.5 --dt 0.0020833333333333333
```

The scene uses a filled disk of radius 0.2 m, a 4 m floor and two 3 m side walls.
The dashed upper guide is explicitly non-colliding. All scene geometry is created
once in world meters; display-only colors, pixel widths, and framing stay in
`rendering.py`. The circle actor's position changes; its mesh is not rebuilt.
An orthographic camera looks along -z at the x-y plane with +y upward. Mouse
rotate/pan/zoom styles and default view-changing keyboard callbacks are disabled.
Q, Escape, and the window close button exit. The initial framing is fixed; a very
narrow resized window may crop the sides rather than automatically move the camera.

A native repeating timer requests display updates every 16 ms, but actual elapsed
time comes from `perf_counter`, not the requested timer interval. Timing starts
at the first callback, excluding scene setup. `FixedStepScheduler.advance(elapsed)`
accumulates elapsed seconds and calls the production `complete_step` only with the
unchanged selected dt. It renders the latest completed state once per timer
callback, with no interpolation. Ordinary expose/resize events may also repaint.

At most 60 physics steps run per callback. Excess whole steps are discarded and
their time is accumulated; the fractional remainder is retained. Near timestep
boundaries, an eight-ulp normalization prevents roundoff alone from losing a step.
Overload makes simulation time lag wall time; it never increases dt. The window
shows accumulated discarded time, and shutdown prints total steps, simulated time,
discarded time/steps, and remainder. The native event loop remains active between
short callbacks. Closing the plotter tears down its interactor and timer; callback
exceptions end the event loop and are re-raised with their original traceback.

`check_scheduling.py` uses synthetic intervals and imports no PyVista. It checks
insufficient/fractional elapsed time, identical physics state for different display
intervals, the 60-step cap, discarded whole steps, preserved remainder, invalid
elapsed time, and unchanged dt. Expected overload example: dt=0.01 s and elapsed
1.2575 s produces 60 steps, discards 0.65 s, and retains 0.0075 s. These are
expectations, not claimed local results. Timing comparisons allow 1e-12 s roundoff.

API references: [PyVista repeating timers](https://docs.pyvista.org/api/plotting/_autosummary/pyvista.renderwindowinteractor.create_timer),
[interactor style](https://docs.pyvista.org/api/plotting/_autosummary/pyvista.renderwindowinteractor.style),
and [Plotter.show](https://docs.pyvista.org/api/plotting/_autosummary/pyvista.plotter.show).
The API use was also checked against the v0.46.3 upstream interactor source;
compatibility with the actual installed PyVista/VTK versions still requires the
following local checks. No offscreen image substitutes for the interactive test.

### Local Stage 5 verification

```text
python --version
python check_integration.py
python check_contacts.py
python check_scheduling.py
python check_cli.py
python make_figures.py --output-dir figures_stage5
python main.py
python main.py --restitution 0.5 --dt 0.0020833333333333333
```

For each GUI run, record actual startup versions, arguments, observed behavior,
shutdown output, and any traceback. Check:

- Default motion starts at (1, 2) m, moves right/down, and bounces off floor and
  both walls. Observe at least 10 simulated seconds to see both side walls.
- The disk diameter is 0.4 m (one tenth of the 4 m floor); it stays circular and
  touches the floor/walls at its edge. The dashed top is labeled non-colliding.
- Drag each mouse button, use the wheel and modifiers, and press R/V/X/Y/Z:
  the camera should not rotate, pan, zoom, or change projection.
- Changed restitution produces lower bounces; the displayed dt and e match the
  second command. Meshes do not visibly flicker or rebuild.
- The window responds to move/resize and closes without a hanging process or
  traceback. Exercise the close button, Q, and Escape across separate runs.
- If overload occurs, discarded time increases while motion remains based on
  fixed physics steps. The deterministic overload check supplies repeatable evidence.

All Stage 5 runtime, installed-version, and interactive observations remain pending
until the user supplies the actual local results. No report or deliberate bug work
is included in this stage.

## Plans, review, and evidence

The [original plan](docs/original_plan.md) is unchanged. The
[approved revisions](docs/change_log.md) record both user requests and reasons,
and the final staged workflow. [Provenance](docs/provenance.md) distinguishes
known metadata from unavailable evidence. Complete transcript export remains
outstanding; these documents do not substitute for it.

Each significant task starts from an accepted committed baseline. Show changes
and actual verification results, then wait for user acceptance before committing
or beginning the next stage. Never upload an intentionally broken branch without
explicit authorization. Existing Word files are preserved; temporary files and
the unrelated `test.txt` are excluded from commits.
