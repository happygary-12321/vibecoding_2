# vibecoding_2

Circle simulation assignment. Stage 1 currently provides CLI parsing only.
Physics, contact handling, rendering, numerical checks, and figures are not
implemented yet. Neither entry point opens a window or writes output files.

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

## Module boundaries

Present: `cli.py` owns shared parsing; `main.py` and `make_figures.py` are entry
points. `check_cli.py` is the repeatable Stage 1 verification command.

Planned: `state.py` owns SI-unit state; `integration.py` updates velocity before
position; `contacts.py` corrects floor and side-wall penetration and reflects
only inward normal velocity. `rendering.py` alone owns PyVista, camera, meshes,
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
