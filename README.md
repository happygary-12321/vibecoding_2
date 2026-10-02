# vibecoding_2

Circle simulation assignment. Stage 3 adds floor and side-wall contact handling
and a complete physics step to the SI-unit state and contact-free integrator.
Rendering and figure generation are not implemented yet.
The application entry points retain their Stage 1 unfinished-path behavior;
neither opens a window or writes output files.

## Python and dependencies

Use **Python 3.12.10** consistently. Check `python --version` before running
commands; the unqualified `py` launcher may select a different version.
The current scaffold and its CLI checks need only the Python standard library.
`requirements.txt` lists dependencies planned for later stages; they have not
yet been installed or compatibility-tested in this session.

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
```

Both entry points accept `--restitution` (default 0.8, finite and in [0, 1])
and `--dt` (seconds, default 1/240, finite and greater than zero). Supply a
decimal or scientific-notation number, not a literal expression such as `1/240`.
Invalid inputs exit with status 2. Help exits with status 0. Valid simulation
requests currently print the parsed settings and an explicit **not implemented**
message to stderr, then exit with status 1. That is expected scaffold behavior,
not a completed simulation or a successful numerical validation.

`check_cli.py` requires Python 3.12.10 and checks both help paths, parsed defaults,
custom values, restitution endpoints, invalid numbers, missing values, and
the explicit unfinished-path behavior. It does not test physics.

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
points. `check_cli.py` is the repeatable Stage 1 verification command.

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
Stage 3 runtime verification and regression reruns are pending local execution.

Planned: `rendering.py` alone owns PyVista, camera, meshes,
colors, display settings, and fixed-step real-time scheduling. `validation.py`
will provide deterministic headless checks and plots. No ceiling collision.
Unimplemented modules are not represented by empty placeholder files.

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
