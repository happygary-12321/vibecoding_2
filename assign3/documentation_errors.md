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

## Resolved by Part 4 documentation: extremely large integers

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
- Corrected specification wording (Part 4): "Python int/float values passing
  finiteness and range checks are retained without coercion, excluding bool.
  Explicit validation failures raise ValueError; excessively large integers can
  propagate OverflowError from the finiteness check."
- Status: resolved by documentation in Part 4. Section 4 of `assign3/SPEC.md`
  now distinguishes explicit ValueError checks from possible OverflowError in
  `math.isfinite`; the README includes the same limitation. Existing state
  docstrings already qualify this behavior. No validation code changed.

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

## Corrected in Part 4: stale README instructions and verification scope

- Original wording/location: README opening described "Stage 6 documentation
  and packaging" as under review and called `71834cd` the accepted production
  baseline. Installation/provenance sections stated "Python execution is
  unavailable" and "No new script has yet been executed in the agent session".
- Why incorrect as current guidance: these historical checkpoints do not describe
  the current documentation state. Part 3 is committed at `210030d`; its saved
  verification records actual Python 3.12.10 execution of 19 doctest examples.
- Corrected wording: the README describes current functionality and attributes
  Part 2/3 execution to their stage logs, while keeping final Assignment 3 lint
  and figure comparison explicitly pending. No new Part 4 runtime pass is claimed.
- Original commands/location: README's Stage 6 section instructed readers to run
  `python final_verify.py` and `python build_report.py`.
- Why unusable in this checkout: git status reports these tracked helpers locally
  deleted, alongside packaging/transcript helpers. They were not restored.
- Corrected guidance: list existing entry points and regression scripts; label
  helper absence as audit-time working-tree status and retain historical report
  links without advertising unavailable commands.
- Supporting evidence: current git status/history, root source inventory,
  `assign3/part3_verification.txt`, and actual entry-point source. These are
  documentation corrections, not software fixes or injected-bug experiments.

## Part 5 lint corrections and remaining diagnostics

- Original wording: four regression-class methodName descriptions started with
  "unittest.TestCase"; cli.parse_args and five validation helper return
  descriptions started with lowercase field/formula names.
- Why flagged: numpydoc 1.11.0 PR08/RT04 require initial capitals in prose.
  These were formatting errors, not incorrect numerical claims.
- Correction: "Selector for unittest.TestCase", "Fields ...", "Allowance ...",
  or capitalized "Parameters ..." preserves the documented meaning.
- Original location/omission: local check_cli helpers guarded_import and
  MissingDependency, and validation.write_plots.save had no docstrings (GL08).
  Part 2's public coverage inventory excluded local helpers; full-file lint
  revealed this broader coverage gap.
- Correction: added accurate NumPy-style docstrings for arguments, return value,
  mutation/file effects and actual errors; the local exception documents
  inherited args. No executable statement or assertion changed.
- Evidence: initial and final logs in verification/, the focused
  part5_source_docstrings.patch, unchanged executable ASTs and passing regressions.

At the first Part 5 checkpoint, unsuppressed lint exited 1 with 234 diagnostics: ES01 (76),
SA01 (76), EX01 (73), and PR02 (9). ES01/SA01/EX01 request extended summaries,
cross-reference sections and examples more broadly than the assignment's
applicable-section rule and three-physics-function example minimum. These
stylistic gaps were not hidden or filled with invented material. PR02 reports
real constructor parameters as unknown because the AST linter only reads an
explicit class __init__, not generated dataclass or inherited constructors.
Installed-tool source inspection and actual runtime signatures are recorded in
verification/numpydoc_ast_inspection.txt and runtime_constructor_signatures.json.
The accurate Parameters sections remain. No warning suppression, exclusion,
configuration weakening or monkeypatch was used. Lint is not reported as passed.

Part 5 also replaces README's then-pending final-verification status with actual
results and routes current baseline links to the byte-preserved assign3/before
submission copy. Part 2-4 logs remain unchanged historical records.

## Part 5 review revision: ES01, SA01 and EX01 corrected

- Original omissions/location: 76 object docstrings lacked an extended summary
  (ES01) and See Also section (SA01); 73 lacked an Examples section (EX01).
  The original complete diagnostics remain in verification/lint_explicit_final.log.
- Correction: added role-specific summaries, verified related APIs, and examples
  covering numeric outcomes, state mutation, parser errors, unittest execution,
  and temporary output directories. No constructor or assertion changed.
- Execution: 326 runnable statements across 75 objects passed with zero failures.
  The renderer's example is explicitly manual/unexecuted because it opens a
  native window. Local helper examples execute their containing workflow.
- Supporting implementation: unchanged source call relationships, actual example
  output in verification/examples_*.log, executable AST equality against the
  Assignment 3 starting commit, and non-docstring token equality against HEAD.
- Final raw result: verification/lint_reviewed_all.log contains exactly nine
  PR02 diagnostics, exit 1, and no ES01, SA01 or EX01 findings.
- Distinction: the nine generated/inherited constructor-parameter reports were
  confirmed by review and runtime signatures as checker limitations. Accurate
  Parameters sections remain unchanged by this revision. No suppression,
  constructor modification or numpydoc monkeypatch was introduced.
