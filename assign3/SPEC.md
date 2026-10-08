# 1. Purpose

Describe the simulator currently present at audited commit
`604a32d3d9c8d400a2ecedb7d35f36eee29563fb` on `main`, including its existing
limitations. This is a specification of behavior, not authorization to change it.
The canonical specification is `assign3/SPEC.md`. Paths written as code in this
document are relative to the repository root unless stated otherwise.
The simulator advances one circle under gravity with floor and side-wall contacts,
displays it in a native PyVista window, and provides separate deterministic
headless experiments and plots. Sources: `main.main`, `rendering.run_simulation`,
`make_figures.main`, `validation.run_validation`.

Unmarked implementation statements below are directly grounded in the named
source. Statements about saved runs refer to user-executed evidence in
`evidence/assignment3/before/`, not tests executed while drafting this document.
`[INFERRED]` marks mathematical derivations or interpretations beyond literal
implementation/evidence. Proposed documentation rules and proposed criteria are
requirements for review, not claims of completed implementation or execution.
Equation labels are stable identifiers for subsequent docstrings.
Source notation `module.function` or `module.Class` refers to that symbol in
the root file `module.py`; bare helper names refer to the module named in the
same paragraph. Test classes `IntegrationChecks`, `ContactChecks`,
`SchedulingChecks`, and `CliChecks` reside in `check_integration.py`,
`check_contacts.py`, `check_scheduling.py`, and `check_cli.py`, respectively.

# 2. Non-goals

The current implementation has no ceiling collision, circle-circle collision,
friction, rotation, air resistance, continuous collision detection, adaptive
timestep, or resting-contact threshold. It does not locate an impact within a
timestep or integrate the remaining fraction after impact. Sources:
`integration.step`, `integration.complete_step`, `contacts.resolve_contacts`.

The GUI does not provide parameter widgets or camera interaction; CLI options
are described in Section 4. Headless validation does not test an actual GUI
session. Sources: `rendering.run_simulation`, `cli.parse_args`,
`check_cli.CliChecks`, `validation.run_validation`.

Changes to questionable behavior, physics, or tests are outside this descriptive
specification. Intentional-bug worktrees and duplicate submission directories
are not part of the normal simulator module layout.

# 3. Governing equations

Notation: center position `(x,y)` in m, velocity `(vx,vy)` in m/s, radius `r` in m,
mass `m` in kg, nonnegative gravity magnitude `g` in m/s^2,
restitution `e` dimensionless, fixed timestep `h=dt` in s, box width `W` and
displayed height `H` in m. Superscripts `-` and `+` denote before and after a
contact response; a tilde denotes the integrated, pre-contact state.

**[EQ-MOTION] [INFERRED]** The continuous motion model represented by
`integration.step` is

```text
dx/dt = vx;  dy/dt = vy;  dvx/dt = 0;  dvy/dt = -g.
```

**[EQ-FLIGHT] [INFERRED]** On a contact-free interval measured from its initial
state, this model gives

```text
x(t) = x0 + vx0*t;  y(t) = y0 + vy0*t - g*t^2/2;
vx(t) = vx0;        vy(t) = vy0 - g*t.
```

`validation.free_fall` and `IntegrationChecks.test_free_fall_and_refinement`
directly implement the reference special case `y0=10`, `vy0=0`.

**[EQ-ENERGY]** `validation.energy` computes

```text
E = m*(vx^2 + vy^2)/2 + m*g*y  [J].
```

**[INFERRED]** This expression chooses zero gravitational potential at `y=0`
(not at the resting center height `r`). Under [EQ-MOTION], contact-free
continuous energy is constant; that does not assert discrete conservation.

**[EQ-NORMAL]** `contacts.resolve_contacts` uses normals into the permitted
region: floor `(0,+1)`, left `(+1,0)`, right `(-1,0)`. Its scalar normal
velocities are respectively `vy`, `vx`, and `-vx`. In equivalent notation:

```text
vn+ = -e*vn- if vn- < 0; otherwise vn+ = vn-.
```

Tangential velocity is unchanged. Surface-specific detection and corrections
are specified separately in Section 5.

# 4. Conventions

## Coordinates, types, and validation boundaries

The rendered floor runs from `(0,0,0)` to `(W,0,0)`; side walls are at `x=0,W`.
The circle mesh is centered locally at `(0,0,0)` and translated to `(x,y,0)`.
The camera uses view-up `(0,1,0)`. Thus the floor's left endpoint is the origin;
`x` increases rightward, `y` upward, and `(x,y)` is the circle center, not its
lowest point. Physics is two-dimensional; rendering embeds it at `z=0` without
coordinate scaling or a meters-to-pixels conversion in application code.
Source: `rendering.run_simulation`.

`PhysicsParameters` and `Box` are frozen dataclasses; `CircleState` is mutable.
Their real-valued fields are annotated `float`; Python `int` or `float` values
passing the finiteness and range checks are retained without coercion, excluding
`bool`. `step_count` must have exact type `int` and be nonnegative. Explicit
checks reject unsupported types, bool, nonfinite values and invalid ranges with
`ValueError`. Excessively large integers passed to `math.isfinite` can instead
propagate `OverflowError`. Sources: `state._finite`, dataclass constructors,
`CircleState.validate`.

| Owner / parameter | Default | Unit / accepted range | CLI exposure |
|---|---|---|---|
| `PhysicsParameters.radius` | `0.2` | m; finite, `>0` | None |
| `PhysicsParameters.mass` | `1.0` | kg; finite, `>0` | None |
| `PhysicsParameters.gravity` | `9.81` | m/s^2; finite, `>=0`; magnitude, subtracted from `vy` | None |
| `PhysicsParameters.restitution` | `0.8` | dimensionless; finite, `[0,1]` | `--restitution` on both entry points |
| `PhysicsParameters.dt` | `1.0/240.0` | s; finite, `>0` | `--dt` on both entry points |
| `CircleState.x`, `y` | `1.0`, `2.0` | m; any finite values | None |
| `CircleState.vx`, `vy` | `1.5`, `0.0` | m/s; any finite values | None |
| `CircleState.step_count` | `0` | dimensionless integer count, `>=0` | None |
| `Box.width`, `height` | `4.0`, `3.0` | m; finite, `>0` individually | None |
| Figure free-fall duration | `1.0` | s; finite, positive, additional constraints below | `--duration`, figures only |
| Figure bounce duration | `10.0` | s; finite, positive, additional constraints below | `--bounce-duration`, figures only |
| Figure output directory | `"figures"` | path string, relative to process working directory; no parser-level writability check | `--output-dir`, figures only |
| Help | no stored simulation value | `-h` / `--help`, prints help and exits `0` | Both entry points |

Sources: `state.PhysicsParameters`, `state.CircleState`, `state.Box`, `cli.parse_args`.
Initial state and geometry can be supplied to low-level Python interfaces; the
GUI constructs default `CircleState()` and `Box()` internally. They are not GUI
or CLI configuration options. `run_simulation(parameters)` accepts custom physical
parameters through Python. `Box.validate_for(parameters)` separately requires
both dimensions to be strictly greater than `2*r`; `Box()` alone cannot check
this parameter-dependent condition.

`e=0` and `e=1` are accepted; `e<0`, `e>1`, and `dt<=0` are rejected by
`PhysicsParameters` with `ValueError`, and by the CLI with parsing error/status
`2`. CLI numeric strings are converted with `float`, must be finite, and must
meet the applicable range. Expressions such as `1/240` are not evaluated.
Sources: `cli.finite_number`, `restitution_value`, `timestep_value`, `parse_args`.

Figure durations must give integer step counts within eight ulps of
`duration/dt`, at least one and at most `1_000_000` steps per run. Fine free fall
uses `dt/2` and must have exactly twice the coarse count. Free fall is rejected
if `duration >= sqrt(2*(10-0.2)/9.81)` or its predicted coarse endpoint is
`<=0.2 m`. No timestep is silently adjusted. These constraints are enforced in
both figure CLI parsing and `run_validation` via `validate_experiments` and
`whole_steps`; direct helper calls need not pass through those checks.

The following are assumptions rather than universal runtime guarantees:

- `step` does not validate state or parameters. `complete_step` and
  `resolve_contacts` validate geometry, not all state fields. Mutating a
  `CircleState` after construction bypasses checks until `validate()` is called.
- Positions outside the box and above `H` are legal state data; validation does
  not constrain them. `validation.bouncing` explicitly revalidates each result.
- `CircleState.time(parameters)` returns `step_count*dt`; maintaining the same
  `dt` throughout a trajectory is the caller's responsibility.
- Low-level interfaces use ordinary Python objects and annotations, not enforced
  array shapes or automatic unit conversion. Finite initial data do not cause
  `step` to check every subsequent arithmetic result for overflow.

## Experiment and display settings

`validation.free_fall` fixes `(x,y,vx,vy,step_count)=(50,10,0,0,0)` and
`Box(100,100)`. `run_validation` uses the selected `e,h`, then `h/2` for fine
free fall. `validation.bouncing` starts from the default state and box for both
selected `e` and an additional `e=1` run. `contact_direction` fixes `e=0.8`,
`y=0.15 m`, `vy=2 m/s`, with other state/parameter defaults, independently of
CLI restitution. These are experiment constants, not additional CLI options.

The settings below are literal source settings, with no CLI controls or
application-level range validators. Sources: `rendering.FixedStepScheduler`,
`rendering.run_simulation`, `validation.write_plots`.

| Setting | Value and meaning |
|---|---|
| Scheduler constructor inputs | `state`, `parameters`, `box`; no defaults for these objects |
| Scheduler initial bookkeeping | `accumulator=0.0 s`, `discarded_time=0.0 s`, `elapsed_time=0.0 s`, `discarded_steps=0`; fields are `init=False` |
| Per-update cap | `MAX_STEPS_PER_UPDATE=60` physics steps |
| Scheduler rounding | Snap quotient to nearest integer within `8*ulp(quotient)` |
| GUI timer | Repeating `16` ms request; elapsed seconds measured by `perf_counter`; first event starts clock without stepping |
| Window | `(960,800)` pixels, title `Circle in an open box`, `off_screen=False` |
| Disk | Local center `(0,0,0)`, normal `(0,0,1)`, inner radius `0`, outer radius physical `r`, radial resolution `1`, circumferential resolution `96` |
| Colors | Background `#f5f7fa`, disk `#1676b8`, walls/text `#27364b`, upper guide `#929aa6` |
| Mesh display | Disk lighting off; disk, walls, guide non-pickable; wall line width `4` pixels, guide `2` pixels |
| Upper guide | `20` segments at `y=H`; each occupies `0.55` of its `W/20` interval; non-colliding |
| Camera | Position `(W/2,H/2,10)`, focal point `(W/2,H/2,0)`, up `(0,1,0)`, parallel projection; scale `2.2`, clipping range `(0.1,20)` in scene coordinates |
| Text | Fixed scene label at upper left, font size `11`; status position `(12,12)`, font size `10`; label literally says `4 m x 3 m` and `radius 0.2 m` |
| Interaction | Camera style `None`, default key callbacks cleared; `q`, Escape terminate; `show(auto_close=True)`; final `close()` |
| Plot backend / export | Agg; font size `10`; `180` dpi; tight bounding box; constrained layout |
| Plot sizes | Free fall `(9,7)`, free-fall energy `(9,4.5)`, bouncing `(12,8)`, direction `(8,5)` inches |
| Plot styling | Free-fall blue/orange and black reference; bounce impact floor/left/right markers `o`, `<`, `>` with red/green/purple, size `14`; bounce legend font `8`; direction legend font `9`, vertical limits `(-2.2,2.9)` m/s; grid alpha `0.25` |

Physics values are passed directly to the mesh position and dimensions in meters.
Colors, fonts, pixel widths, tessellation counts, and plot layout are display
settings; they are not physics parameters. Timer milliseconds and `perf_counter`
seconds are separate APIs; physics still advances only by `dt` seconds.

# 5. Numerical method

## Integration and time

**[EQ-STEP]** `integration.step(state, parameters)` executes exactly this order:

```text
1. vy <- vy - g*h
2. x  <- x + vx*h
3. y  <- y + vy*h       (uses the updated vy)
4. step_count <- step_count + 1
```

`vx` is unchanged. This is contact-free semi-implicit Euler. It mutates state
and returns `None`. **[EQ-TIME]** `CircleState.time` computes `t=step_count*h`.

`integration.complete_step` validates geometry, calls `step` once, then calls
`resolve_contacts` and returns its list. Contacts therefore see the new position
and velocity, with step count already incremented once. The resolver itself does
not advance time. There is no contact processing before the integration step.

## Detection, correction, and response

The following equations transcribe `contacts.resolve_contacts`. Each detection
is evaluated against the current state at its position in the floor/left/right
sequence. Each correction is recorded even if it is zero. Undetected surfaces
produce no record. Radius offsets the allowed center coordinates from surfaces.

**[EQ-FLOOR]** Floor:

```text
Detection:            y <= r
Position correction:  (dx,dy) = (0,r-y);  y <- r
Velocity response:    if vy < 0: vy <- -e*vy; otherwise unchanged
Recorded normal:      vn = vy
```

**[EQ-LEFT]** Left wall:

```text
Detection:            x <= r
Position correction:  (dx,dy) = (r-x,0);  x <- r
Velocity response:    if vx < 0: vx <- -e*vx; otherwise unchanged
Recorded normal:      vn = vx
```

**[EQ-RIGHT]** Right wall:

```text
Detection:            x >= W-r
Position correction:  (dx,dy) = (W-r-x,0);  x <- W-r
Velocity response:    if vx > 0: vx <- -e*vx; otherwise unchanged
Recorded normal:      vn = -vx
```

`ContactRecord` is frozen and contains `surface` (`"floor"`, `"left"`, `"right"`
as emitted), signed `position_correction` (two-element tuple in m), and scalar
`normal_velocity_before/after` in m/s. It has no own validation. `is_impact`
is the exact inequality `normal_velocity_before != normal_velocity_after`.
Thus touching produces a record even without correction; separating or zero
normal velocity is preserved and is not an impact. For an upward floor overlap,
only `y` is corrected; `vy>0` is preserved. At `e=0`, inward normal speed becomes
zero; at `e=1`, it reverses with equal magnitude. Tangential components remain
unchanged. Sources: `ContactRecord`, `resolve_contacts`,
`ContactChecks.test_surfaces_and_directions`, `test_restitution_endpoints`.

**[INFERRED]** For valid geometry `W>2*r`, changing surface-resolution order
would not change the final physical state: floor edits only `y,vy`, walls edit
only `x,vx`, and the two wall contact regions are disjoint, including after
correction. It would change the returned list order when floor and wall both
contact. Record order is observable and explicitly tested as floor before wall
in `ContactChecks.test_both_corners` and `test_complete_step_order`. This
reasoning is not a proposal to reorder the implementation.

No condition uses `H` to stop upward motion. Side-wall checks also have no
height condition. The GUI draws finite walls to `H` and a dashed upper guide,
but keeps the actor at its physical center without moving the camera.
**[INFERRED]** A circle can pass above the guide, remain visible while inside
the fixed camera view, then leave that view; simulation continues. Positive
gravity still accelerates it downward, and side-wall responses still apply even
above the drawn walls. Sources: `step`, `resolve_contacts`, `run_simulation`.

## Energy and small rebounds

**[EQ-DRIFT]** The expected contact-free drift computed in `validation.free_fall`
and `bouncing` is

```text
Dstep = -m*g^2*h^2/2;  D(t) = -m*g^2*h*t/2, with t=n*h.
```

**[INFERRED]** Substitution of [EQ-STEP] into [EQ-ENERGY] gives these expressions
in exact arithmetic; they describe integration error, not floating-point error.

**[EQ-CONTACT-ENERGY]** `validation.bouncing` computes, per contact,

```text
Kcontact = m*((vn+)^2-(vn-)^2)/2
Lcontact = -m*(1-e^2)*(vn-)^2/2 if vn- < 0, else 0
Ccontact = m*g*dy
```

**[EQ-ACCOUNTING]** Its step and cumulative expected changes are

```text
Eafter - Ebefore = Dstep + sum(Lcontact) + sum(Ccontact)
Eafter - Einitial = sum(Dstep) + sum(Lcontact) + sum(Ccontact).
```

The code measures residuals against these equalities and reconstructs pre-contact
energy as `Eafter-sum(Kcontact)-sum(Ccontact)`. **[INFERRED]** Floor position
correction adds potential energy by moving the center upward; this is a discrete
correction artifact, not physical restitution loss. At `e=1`, restitution loss
is zero, but integration drift and correction energy remain, so exact total
energy conservation does not follow. The saved elastic energy plot also shows
nonconstant energy.

There is no sleep, sticking mode, velocity cutoff, or rest detection in
`complete_step` or `resolve_contacts`. The saved default 10-second run records
`1172` floor impacts; its last sample is `y=0.2 m`,
`vy=0.01816666666666666 m/s`, `step_count=2400`. Source:
`evidence/assignment3/before/figures/results.json`, `bouncing[0]`.

**[EQ-MICROBOUNCE] [INFERRED]** If a step begins at `y=r` with upward velocity
`u<g*h`, integration penetrates the floor and restitution gives
`u_next=e*(g*h-u)`. The fixed point is `u*=e*g*h/(1+e)`, approximately
`+0.0181666667 m/s` at defaults. For `0<=e<1`, deviations in this repeated-contact
regime multiply by `-e`. This explains the saved late nonzero velocity; it does
not establish exact rest or a universal trajectory for every input. At `e=0`
and positive gravity, each complete step can finish at `y=r,vy=0` while gravity
and contact correction still act on the next step.

**[INFERRED]** In the ideal continuous flight/instantaneous-impact model,
successive rebound speeds scale by `e` and heights by `e^2`; for `0<e<1` they
tend to zero. Continuing after the accumulation of impacts requires a resting
contact convention. That convention is absent here, and the discrete algorithm
must not be described as implementing ideal continuous settling.

**[INFERRED]** For `g > 0` and an initial upward rebound speed `u0 > 0`,
successive flight times are `2*u0*e^k/g`, for `k = 0, 1, 2, ...`.
For `0 < e < 1`, their sum is `2*u0/[g*(1-e)]`, so infinitely many
ideal impacts accumulate within a finite time. This interval starts
immediately after the rebound defining `u0` and excludes the preceding
initial fall. The fixed-timestep implementation does not resolve
this continuous-time accumulation.

## Scheduler

`FixedStepScheduler.advance(elapsed)` requires finite, nonnegative elapsed
seconds and a finite `(accumulator+elapsed)/dt`, otherwise raises `ValueError`.
It rounds the quotient to the nearest integer only within eight ulps; otherwise
it floors it. It runs `min(available,60)` complete steps, discards all remaining
whole steps, and stores `max(0,total-available*dt)` as the fractional remainder.
It increments discarded-step/time counters and elapsed wall time; it never
increases `dt` to catch up. The first GUI timer event only sets the clock.
Source: `rendering.FixedStepScheduler.advance`, `run_simulation.update`.

**[INFERRED]** Dropped time is not simulated later, so under overload simulation
time lags elapsed wall time. At default `dt`, one update advances at most
`60/240=0.25 s`. Requested timer spacing is not a guarantee of display frequency.

# 6. Interfaces

The normal layout is the following root-level Python modules. Duplicate
`huang_yuxuan_hw2/` files and `.bug-worktrees/` experiments are excluded.

**Audit-time working-tree status:** `build_report.py`, `final_verify.py`,
`package_submission.py`, and `preserve_transcript.py` are tracked in the audited
commit but were absent from the local working tree during the audit. Their
absence is an audit-time observation, not a permanent module-layout decision.

In the interface summaries, `p` abbreviates the argument named `parameters`;
it is not an alternative keyword accepted by the functions.

| Module / public interface | Inputs, outputs, mutation and side effects |
|---|---|
| `state`: `PhysicsParameters`, `Box`, `CircleState` | Scalar fields in Section 4; constructors validate and may raise `ValueError`. `Box.validate_for(p)` and `CircleState.validate()` return `None` or raise. `CircleState.time(p)` returns scalar seconds without mutation. |
| `cli`: `finite_number(text)`, `restitution_value(text)`, `timestep_value(text)` | Strings to floats; malformed, nonfinite or out-of-range values raise `argparse.ArgumentTypeError`. |
| `cli.parse_args(description, argv=None, *, figures=False)` | Description string, optional list of argument strings (`None` uses process arguments), boolean mode; returns `argparse.Namespace`. Prints help/errors; argparse raises `SystemExit(0/2)`. |
| `integration.step(state,p)` | Mutates center, vertical velocity and count; returns `None`; no contact or I/O. |
| `integration.complete_step(state,p,box)` | Geometry validation, one integration, contact resolution; mutates state; returns `list[ContactRecord]`; invalid geometry raises `ValueError` before mutation. |
| `contacts.resolve_contacts(state,p,box)` | Mutates contacted coordinates/normal velocities; returns ordered records, possibly empty; no time advancement or I/O; invalid geometry raises `ValueError`. |
| `contacts.ContactRecord.is_impact` | Read-only boolean property comparing the recorded velocities. |
| `rendering.FixedStepScheduler(state,p,box).advance(elapsed)` | Constructor validates state and geometry. `advance` returns integer executed-step count and mutates state and scheduler counters; no GUI by itself. See Section 5 for errors and discard behavior. |
| `rendering.run_simulation(parameters)` | Returns `None` after a blocking GUI session; creates default state/box, scene, timer and actor; prints versions/settings/final counters; closes plotter. Imports PyVista lazily. Missing `pyvista`, `vtk` or `vtkmodules` raises `RenderingDependencyError`; timer creation failure raises `RuntimeError`; unexpected errors propagate, including callback errors re-raised after loop termination. |
| `main.main(argv=None)` | Parses options, creates parameters, then imports rendering and launches GUI. Returns `0` normally or `1` for caught `RenderingDependencyError` with stderr message. Other errors propagate; script guard uses `SystemExit(main())`. |
| `make_figures.main(argv=None)` | Parses figure options and calls `run_validation`; prints result summaries; returns `0` for passed report, `1` for failed report or caught `OSError`. Parsing exits `0/2`; script guard uses `SystemExit(main())`. |
| `validation.run_validation(output_dir,restitution,dt,duration,bounce_duration)` | All five arguments required in Python API; returns nested report dictionary; writes output directory/files, gathers environment versions, runs integration/contact suites, experiments and plots. Detailed effects below. |
| `check_integration`, `check_contacts`, `check_scheduling`, `check_cli` | `unittest.TestCase` classes and script entry guards; guards require Python exactly `3.12.10`. CLI checks launch subprocesses and a temporary-directory figure run; scheduler checks use synthetic elapsed times without GUI. |

`validation` also exposes non-underscore helpers:

- `whole_steps(duration,dt,option)` returns an integer count;
  `validate_experiments(dt,duration,bounce_duration)` returns a three-integer
  tuple `(coarse,fine,bounce)`; invalid experiments raise `ValueError`.
- `tolerance(base,count,scale)` returns a scalar allowance;
  `check_close(checks,name,measured,expected,tol)` and
  `check_true(checks,name,measured)` append result dictionaries to the supplied
  list and return `None`.
- `energy(state,p)` returns joules; `sample(state,p)` returns a dictionary of
  time, state fields and energy, without advancing state.
- `free_fall(p,count,checks,label)` and `bouncing(p,count,checks,label)` create
  local states, advance them, append checks, and return dictionaries containing
  parameters and `count+1` samples including time zero. Bouncing also returns
  contact records/counts. `contact_direction(checks)` returns the fixed overlap
  diagnostic dictionary and appends its checks. These helpers assume suitable
  counts/parameters; they do not all enforce CLI duration constraints.
- `regression_checks(output)` expects a `Path`, writes `regression_checks.txt`
  and returns test counts/status/failure details; it loads only integration and
  contact suites, not CLI/scheduler suites.
- `write_plots(report,output)` expects the populated report and output `Path`,
  selects Agg, changes Matplotlib font settings, writes four PNGs, closes its
  figures, updates report backend metadata, and returns saved filenames.

`run_validation` writes `results.json` initially with status `running`, then
updates it to `passed` or `failed`. It records units, parameters, durations,
Python/executable/dependency versions, checks, tolerances, numerical traces,
contact data, and output filenames. Exceptions inside its experiment/plotting
`try` block are caught and stored as a traceback with failed status. Validation,
directory creation, initial write and final JSON write are outside that block
and can propagate errors. Final JSON serialization uses `allow_nan=False`.
Sources: `validation.run_validation`, `make_figures.main`.

Output names are `free_fall.png`, `free_fall_energy.png`, `bouncing_energy.png`,
`contact_direction.png`, `results.json`, and `regression_checks.txt`. Existing
same-named outputs are overwritten; the directory is not cleared first, so a
failed run may leave old PNGs. The direction figure's faulty line is an isolated
illustration, not an injected defect in the production resolver.

Physics uses the standard library. Headless plotting requires Matplotlib;
rendering requires PyVista/VTK. Requirements files declare `matplotlib`,
`pyvista>=0.46.3`, and report tooling `reportlab,pypdf`; the combined requirements
file includes all three lists. The test script version guards do not mean every
runtime entry point enforces Python `3.12.10`. Sources: requirements files and
the four `check_*.py` script guards.

# 7. Documentation conventions

The next stage shall use NumPy-style docstrings. These are documentation
requirements; current docstrings are not claimed to comply already.

- Start with a short behavior summary. Use applicable `Parameters`, `Returns`,
  `Attributes`, `Raises`, `Notes`, and `Examples` sections with NumPy-style
  underlined headings; omit irrelevant empty sections.
- Specify types, units and constraints beside each parameter/attribute. State
  that restitution/counts are dimensionless; distinguish seconds from timer
  milliseconds and scene meters from pixel/font settings. Document tuple shape
  `(2,)` for corrections and `(3,)` for scene coordinates; do not imply NumPy
  arrays where code uses tuples, scalars, lists or dictionaries.
- Document dataclass defaults, frozen/mutable status and constructor validation
  in `Attributes` or constructor parameters. Distinguish checked constraints
  from caller responsibilities and unvalidated post-construction mutation.
- Document actual return values, including `None`, integer status/counts,
  record-list order, and important nested dictionary keys. For mutating methods,
  explicitly name changed state/counters and whether time advances.
- State side effects in `Notes`: files created/overwritten, printing, imports,
  global plotting settings, GUI blocking/resources and cleanup. Do not call
  figure-generation examples side-effect-free.
- List actual deliberate exceptions and relevant propagated errors; distinguish
  CLI `SystemExit`, caught errors converted to status `1`, and failed-report
  exceptions. Do not invent exception guarantees for arbitrary invalid objects.
- Reference the stable labels in this specification (for example,
  `assign3/SPEC.md [EQ-STEP]`, `assign3/SPEC.md [EQ-FLOOR]`,
  `assign3/SPEC.md [EQ-ACCOUNTING]`) alongside readable equations
  where helpful. Retain `[INFERRED]` when explaining a derivation rather than a
  directly implemented check. Do not invent a design rationale.
- Examples must include imports/setup, use valid inputs, and show real return or
  mutation semantics. Prefer small deterministic examples with approximate
  float comparisons. Label GUI/file-writing examples and use a fresh temporary
  output directory for validation examples, never the saved before-baseline.
  Do not claim an example was executed unless it actually was.
- At least three public functions or methods in `state.py`, `contacts.py`, or
  `integration.py` must have runnable doctest examples. Those examples must be
  executed during the later docstring verification stage. This is a requirement,
  not completed documentation or verification work.

# 8. Validation criteria

## Existing numerical criteria

`validation.check_close` requires a finite residual whose absolute value is at
most its tolerance. **[EQ-TOL]** `validation.tolerance` computes
`max(base,8*epsilon*N*max(1,scale))`, using `sys.float_info.epsilon` and step
count `N`. This is applied to numerical values expressed in the stated SI unit.
Free fall uses bases `1e-10 m`, `1e-10 m/s`, `1e-9 J`, and scales `10`, `g*N*h`,
and initial energy respectively. Bouncing uses base `1e-9 J` and the maximum
absolute sampled energy as scale. Sources: `free_fall`, `bouncing`, `tolerance`.

**[INFERRED]** These tolerances bound floating-point residuals relative to
discrete formulas; they do not bound the entire integration error against the
continuous solution. In particular, `1e-10 m` does not mean the default
trajectory is within `1e-10 m` of analytical free fall.

| Criterion / setup and interval | Measured quantity and expected result | Allowance / supporting source |
|---|---|---|
| One contact-free step, default state except `vy=3`, count `7`, `h=0.1 s` | After one step: `vy=2.019 m/s`, `x=1.15 m`, `y=2.2019 m`, count `8`, time `0.8 s`; `vx=1.5` unchanged | `1e-12` in relevant SI unit; exact count and `vx`; `IntegrationChecks.test_one_step` |
| Zero gravity, `h=0.01 s`, `vx=-2`, `vy=3`, default position, `100` steps / `1 s` | Final `x=-1 m`, `y=5 m`; velocities unchanged | `1e-10 m`, exact velocities/count/time; `test_zero_gravity` |
| Free fall from `(50,10)`, zero velocity, box `(100,100)`, `h=1/240` and `1/480`, `0..1 s` | Every-sample signed error `y-(10-g*t^2/2)` equals `-g*h*t/2`; endpoint heights `5.0745625`, `5.08478125 m`, velocity `-9.81 m/s` | Integration test: `1e-10 m`/`m/s`; validation: [EQ-TOL]; `test_free_fall_and_refinement`, `validation.free_fall` |
| Refinement on the same interval, coarse samples paired with every second fine sample | Coarse signed error minus twice fine error equals zero; endpoint error ratio equals `2`; matched times equal | Integration test: `3e-10 m`, ratio `1e-7`; validation: coarse position tolerance plus twice fine tolerance, time `1e-12 s`; `test_free_fall_and_refinement`, `run_validation` |
| Contact-free energy, same two free-fall runs, including time zero | Each step and cumulative drift follow [EQ-DRIFT]; final expected drifts `-0.200491875 J`, `-0.1002459375 J` | Energy [EQ-TOL], maximum residual over all samples; `validation.free_fall` |
| Bouncing from default state/box, selected `e=0.8` and diagnostic `e=1`, `h=1/240`, `0..10 s` | Reconstructed integration drift, each contact kinetic loss and step/cumulative accounting follow [EQ-DRIFT], [EQ-CONTACT-ENERGY], [EQ-ACCOUNTING]; elastic restitution sum is zero | Energy [EQ-TOL]; maxima across steps/contacts, cumulative residual included; `validation.bouncing` |
| Same bouncing runs | State remains finite, `y>=r`, `r<=x<=W-r`; default contact test also requires all three impact surfaces and sequential counts `1..2400` | Boolean/exact checks; `validation.bouncing`, `ContactChecks.test_default_trajectory` |
| Direct floor overlap, `y=0.15`, `vy=+2`, `e=0.8`, no time advancement | `y=0.2 m`, `vy=+2 m/s`, one floor record, no impact | `1e-12` SI and exact booleans; `validation.contact_direction`; this is an EXISTING criterion |
| Direct touching/overlap at each surface; normal speeds `-2,+2,0`, `e=0.8` | Normal outputs `+1.6,+2,0 m/s`; boundary correction, signed record, tangent and count preservation; both corners floor-first | `1e-12` SI, exact order/flags/count/tangents; `ContactChecks.test_surfaces_and_directions`, `test_both_corners`; endpoints `e=0,1` in `test_restitution_endpoints` |
| Synthetic scheduler intervals totaling `1 s` at default `h`; no GUI | `[0.01]*100`, `[0.04]*25`, `[0.1]*10` produce identical state, `240` steps, no discard | Exact state/count, remainder `1e-12 s`; `SchedulingChecks.test_display_interval_independence` |
| Scheduler overload: `h=0.01`, elapsed `1.2575 s`, then `0.0025 s` | First call executes `60`, discards `65` steps / `0.65 s`, retains `0.0075 s`; next executes one; elapsed equals simulated + discarded + remainder | Exact counts, `1e-12 s`; `test_cap_discard_and_remainder`; exact-cap behavior in `test_exact_cap_does_not_discard` |

The signed-height-error and drift formulas in the table are literal expected
expressions in existing checks. **[INFERRED]** Their derivation follows
[EQ-STEP]: after `n` contact-free steps,
`y_n=y0+n*h*vy0-g*h^2*n*(n+1)/2`; subtracting [EQ-FLIGHT] at `t=n*h` yields
`-g*h*t/2`.

CLI criteria include valid defaults/custom values/endpoints; invalid numbers,
missing values and invalid durations exit `2`; help exits `0`; GUI parameter
forwarding is checked with mocks. `CliChecks.test_headless_figures` uses
`h=0.02`, durations `0.2 s`, `e=0.25`, and a temporary directory, requiring a
passed report, four PNG signatures, regression log, Agg and no rendering/PyVista
imports. It is not a GUI test. The main headless validator also explicitly
checks loaded modules for `rendering` and `pyvista` names.

## Saved evidence and limits

`evidence/assignment3/before/commit.txt` identifies the audited commit.
`make_figures.exit.txt` contains `0`; `make_figures.log` reports success;
`figures/results.json` reports `passed`, all `26` checks passing and `11`
integration/contact regressions passing. Recorded Python is `3.12.10`,
Matplotlib `3.10.7`, NumPy `2.3.5`, backend Agg. The four PNGs, JSON and
regression log are present. These are saved user-run results, not execution by
the drafting agent; no GUI/CLI/scheduler pass is inferred from these 11 tests.

The saved log does not record the exact shell command.

**Audit-time working-tree status:** Saved `git_status.txt`
marks `figures/regression_checks.txt` modified while the accepted audit's live
status does not; its saved copy and current file matched byte-for-byte in that
audit. The cause of the historical status difference is unresolved. The saved
baseline must remain unchanged.

## New proposed floor-bounce criterion (not yet executed)

**[EQ-FIRST-IMPACT] [INFERRED]** With default state and parameters, before first
contact the discrete center height is
`y_n=2-(9.81/240^2)*n*(n+1)/2`. Therefore the first floor-impact index should be
the smallest positive integer with `y_n<=0.2`:

```text
n* = ceil((-1 + sqrt(1 + 8*(2-0.2)/(9.81*h^2)))/2) = 145
y_144 = 0.2219375 m > 0.2 m
y_145 (before correction) = 0.1972421875 m <= 0.2 m
t_145 = 145/240 s = 0.6041666666666666... s
vy_before = -145*9.81/240 = -5.926875 m/s
vy_after = -0.8*vy_before = +4.7415 m/s
dy = 0.2-y_145 = 0.0027578125 m.
```

**[INFERRED] Proposed acceptance criterion:** Starting from default objects,
call `complete_step` through step `145`; require no floor record on steps
`1..144`, and exactly one impact floor record at step `145`. Require corrected
`y=0.2 m`, the above normal velocities/correction, and time `145/240 s`.
Use exact step/order/flag checks, proposed absolute tolerance `1e-10 m` and
`1e-10 m/s` for accumulated quantities and `1e-12 s` for time. Horizontal
position at this event is `1+1.5*(145/240)=1.90625 m`, safely between the walls;
there should be no wall record in this interval. This is a mathematical
prediction and proposed test, not a newly executed test.

Novelty was checked against all four root `check_*.py` files and
`validation.py`: existing contact tests cover direct responses, corners, one
constructed complete step, and a bounded 2400-step trajectory, but do not
assert the default first-impact index or its velocity. `validation.bouncing`
records contacts and checks accounting without this event-timing assertion.
The saved first floor record already contains step `145` and velocity `4.7415`;
that observation corroborates the prediction but does not turn this proposed
criterion into an implemented or executed assertion. No test is added here.

# 9. Open questions

These items are documentation limitations/candidate Known Issues, not fixes
authorized by this specification.

- **Small rebounds:** [INFERRED] [EQ-MICROBOUNCE] explains continued floor
  impacts and nonzero late velocity. Should later documentation call this
  persistent contact jitter? Preserve the existing algorithm and saved values.
- **Contact geometry:** Side-wall checks apply above the finite drawn walls;
  the top guide has no collision. [INFERRED] This can differ from a reader's
  interpretation of a finite-height open box. Document both behaviors explicitly.
- **Energy:** [INFERRED] Discrete drift/correction preclude an exact-conservation
  claim even at `e=1`. No tolerance should disguise that model limitation.
- **Scheduling:** Whole-step backlog beyond `60` is discarded. This is current
  behavior, not a promise to track wall time under arbitrary load.
- **Programmatic rendering parameters:** The scene label literally states
  radius `0.2 m` although `run_simulation` accepts custom parameters.
  [INFERRED] A different Python-supplied radius can make that label inaccurate.
- **Validation bounds:** Duration and geometry checks are explicit; low-level
  mutation and extreme finite arithmetic are not comprehensively guarded.
  No behavior change is proposed to add guards.
- **Unexecuted reasoning:** Corner-order independence, the microbounce fixed
  point and the new first-impact criterion are labeled derivations. The proposed
  criterion remains unimplemented/unexecuted; no new GUI observation verifies
  off-screen behavior. No design rationale is asserted for these choices.
- **Provenance:** Exact baseline shell command and historical regression-log
  status discrepancy remain unresolved. Preserve the complete Assignment 3
  transcript alongside the saved before-evidence.
