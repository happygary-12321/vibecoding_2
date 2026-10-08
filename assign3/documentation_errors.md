# Actual agent-written documentation errors

This record separates factual documentation corrections from unchanged software
limitations. Locations use repository-relative paths. No intentional Assignment 2
bug experiment is counted as a current documentation error.

## Corrected: Part 1 first-impact arithmetic

- Original wording/location: the initial, uncommitted root `SPEC.md`, Section 8,
  stated `y_144 = 0.221875 m > 0.2 m`.
- Why incorrect: substitution into the stated discrete free-fall formula gives
  `2 - (9.81/240^2)*144*145/2 = 0.2219375 m`.
- Support: `integration.py: step` and the derivation of `[EQ-FIRST-IMPACT]`.
  This arithmetic was checked during Part 1; it was not a new simulation run.
- Corrected wording: `y_144 = 0.2219375 m > 0.2 m`.
- Status: corrected before Part 1 acceptance; the committed `assign3/SPEC.md`
  already contains the corrected value and was not edited in Part 2.

## Corrected: CLI dependency description

- Original wording/location: `cli.py` module docstring at the Part 2 starting
  commit: "Shared command-line parsing, independent of physics and rendering."
- Why incorrect: figure-mode parsing imports `validation.validate_experiments`;
  `validation.py` imports physics modules. The parsing path therefore has a
  deferred physics-module dependency, although it does not advance the simulator.
- Support: `cli.py: parse_args` under `if figures`, and imports in `validation.py`.
- Corrected wording in the module Notes: "Figure-mode parsing imports validation
  to check durations; it does not run experiments or open a GUI."
- Status: corrected by the Part 2 docstring edit; imports are unchanged.

## Corrected: overly broad renderer-update description

- Original wording/location: the first Part 2 draft of
  `rendering.py: run_simulation` Notes said "Only actor position changes during
  updates; the disk mesh is not rebuilt."
- Why incorrect: the nested `update` callback also updates the status text and
  renders the scene. The restriction applies to disk geometry, not all GUI state.
- Support: the callback calls `status.SetInput(...)` and `plotter.render()`
  after assigning `actor.position`.
- Corrected wording: "For the disk, only actor position changes; its mesh is not
  rebuilt. Updates also change the status text and render the scene."
- Status: corrected during manual diff review, without changing the callback.

## Specification discrepancy pending review: extremely large integers

- Original wording/location: accepted `assign3/SPEC.md`, Section 4, says
  constructors "accept finite Python int or float values without coercion" and
  "Invalid values raise ValueError."
- Why this needs qualification: `state.py: _finite` calls `math.isfinite(value)`.
  An excessively large Python integer can raise `OverflowError` during that
  call rather than reach the explicit `ValueError` checks. Accepted values are
  retained without coercion, but not every mathematically finite integer passes.
- Support: the unchanged `_finite` implementation; an executed Python 3.12.10
  check of `math.isfinite(10**1000)` raised `OverflowError`, recorded in
  `assign3/part2_verification.txt`.
- Proposed corrected specification wording: "Python int/float values passing
  finiteness and range checks are retained without coercion, excluding bool.
  Explicit validation failures raise ValueError; excessively large integers can
  propagate OverflowError from the finiteness check."
- Status: the new state docstrings qualify integer acceptance and document
  `OverflowError`. The accepted specification is unchanged; its qualification
  remains pending for a later documentation revision.
  This is a documentation qualification, not a request to change validation.

## Corrected: incomplete class-docstring Attributes coverage

- Original location: Part 2 class docstrings for
  `rendering.RenderingDependencyError`, `check_cli.CliChecks`,
  `check_contacts.ContactChecks`, `check_integration.IntegrationChecks`,
  and `check_scheduling.SchedulingChecks` omitted an Attributes section.
- Original wording: the exception Notes said it "adds no attributes or custom
  constructor"; the check classes said they inherit unittest lifecycle and
  assertion state with "no additional persistent data attributes".
- Why incomplete: these descriptions did not satisfy the explicit class
  Attributes requirement. Inherited attributes still exist. The earlier
  docstring-presence coverage count was not evidence of section completeness.
- Supporting implementation: RenderingDependencyError inherits RuntimeError
  and its `args` tuple; all four check classes inherit unittest.TestCase's
  `failureException`, `longMessage`, and `maxDiff` settings without overrides.
- Corrected documentation: each class now has an Attributes section. The
  exception documents its inherited `args`; the check classes document the
  inherited defaults AssertionError, True, and 640 characters (or None to
  disable the diff limit). No attributes or executable statements were added.
- Verification results for this revision are recorded in
  `assign3/part2_verification.txt`; numpydoc lint remains pending.

## Existing software limitations, not documentation mistakes

Persistent small floor rebounds, integration/position-correction energy
artifacts, side-wall response above the drawn walls, scheduler backlog discard,
and the literal default-radius GUI label are existing behaviors. They remain
unchanged and are documented as limitations. No fixes are included.

The proposed first-floor-impact criterion remains unimplemented and unexecuted.
The saved Assignment 3 before-evidence remains user-run evidence; it is not
reported as agent-executed testing.
