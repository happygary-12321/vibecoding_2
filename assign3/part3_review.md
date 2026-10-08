# Assignment 3 Part 3 comment review

Accepted baseline: `fd1192f5b13c10936710525f1e2cd36c82302ac9`
(`docs: document simulator APIs with NumPy-style docstrings`).
Part 2 was committed and all 12 source files matched that commit before this
stage. On resumption, no Part 3 source edits or artifacts were present.

## Reviewed files and decisions

| File | Review outcome and code-based justification |
| --- | --- |
| main.py | Unchanged. The deferred rendering import already has a useful explanation; dispatch and returned status are documented. |
| make_figures.py | Unchanged. Existing docstrings explain validation invocation, status, and propagated errors; extra comments would repeat them. |
| cli.py | Unchanged. Range checks and figure-mode duration validation are explicit and documented. |
| state.py | Unchanged. Units, type/range constraints, and time calculation are documented; no unclear ordinary comments needed removal. |
| integration.py | Added local ordering explanations: `step` updates vy before y; `complete_step` increments the count through integration before resolving endpoint contacts. No event-time subdivision occurs. |
| contacts.py | Explained radius-based edge tests, inclusive touch, projection independent of velocity, inward-only restitution, right-wall normal sign, record order, corner independence, persistent rebounds, and missing ceiling/height cutoff. `resolve_contacts` contains exactly these branches. |
| rendering.py | Explained the eight-ulp threshold, 60-step work cap, subtraction of all available whole steps, and fractional remainder clamp in `FixedStepScheduler.advance`. Grouped display settings by effect and described callback exception transport without asserting external VTK internals. |
| validation.py | Explained duration alignment and floor guards, scale-dependent residual allowances, potential energy from projection, elastic diagnostic limitations, matched refinement samples, and plotting-only settings. Existing reconstruction and work-cap comments remain useful. |
| check_cli.py | Unchanged. Existing method documentation explains mocks, parser failures, and assertions; no additional comment is needed. |
| check_integration.py | Explained the combined refinement allowance and roundoff amplification in the endpoint ratio; preserved assertions and independently calculated reference values. |
| check_contacts.py | Removed two inline comments that repeated the method documentation (ten-second duration and state validation). Kept useful units, tuple schema, and constructed-step derivations. |
| check_scheduling.py | Explained that fractional-time allowances do not relax integer step counts or state equality. |

The source patch contains changes to seven files; all twelve were reviewed and
compared. Docstrings, executable tokens, signatures, imports, constants, and
test assertions remain unchanged. Existing useful units and equation references
were retained. No encoding declarations or operational/tool directives changed.

## Derived explanations and rationale limits

- [INFERRED] Corner response independence follows from separate x/y mutations
  and the validated width greater than the diameter. Reordering floor and wall
  responses can change record order without changing the final physical state.
- [INFERRED] The coarse free-fall endpoint is lower than the fine/continuous
  endpoint by the formulas in `assign3/SPEC.md` [EQ-FLIGHT]. The endpoint
  guard therefore supplements the continuous fall-time guard.
- [INFERRED] One coarse allowance plus twice the fine allowance bounds their
  weighted residual. Division by the small endpoint error amplifies absolute
  roundoff. This explains the effect of the ratio tolerance, not a verified
  historical reason for choosing exactly 1e-7.
- The numerical choices 60, eight ulps, and the tolerance factor eight are
  existing policies. No benchmark or rigorous universal error bound is claimed.
- Mesh tessellation, dashed-guide spacing, camera framing/clipping, font sizes,
  figure sizes, DPI, and timer interval have observable display effects.
  Historical reasons for their exact numerical values are not established.
- Earlier renderer comments asserted that setting the style prevents
  `show()` restoring it, that VTK swallows callback exceptions, and that
  closing tears down particular internals. These library-specific assertions
  were not verified here. Comments now describe assignments, stored failures,
  re-raising, and explicit closing visible in this repository. This is a
  qualification of unsupported rationale, not evidence those assertions were
  false. No GUI or external-library behavior experiment was run.

## Reserved for later README Known Issues

These are existing limitations, not fixes or newly executed experiments.

- Small floor rebounds persist; there is no resting-speed threshold. Saved
  user-run default 10-second evidence records 1,172 floor impacts and late vy
  near +0.0181667 m/s. This stage did not rerun that trajectory.
- Contact-free Euler drift and projection-induced potential energy remain
  separate from restitution loss; e=1 does not ensure total-energy conservation.
- There is no ceiling and side walls respond above their finite drawn height.
  The fixed camera can leave high positions outside the visible frame.
- More than 60 available steps in a display update causes whole-step backlog
  discard, so simulation time can lag supplied elapsed time.
- The renderer's literal radius label remains 0.2 m for custom Python parameters.
- Extremely large integer inputs can propagate OverflowError through
  `state._finite`. The accepted SPEC qualification remains pending for a
  later documentation revision; SPEC was not changed.
- Figure generation does not clear its output directory before a run; old
  figures may remain if a later run fails. No figure generation occurred here.

No newly established factual documentation error required correction in
`documentation_errors.md`; that file is unchanged. Unverified historical
rationale is recorded above rather than presented as a proven error.

## Verification and preservation

See `part3_verification.txt` for the exact executed verification program and
output, and `part3_source_diff.patch` for the complete focused source diff.
Full AST comparisons retain docstrings and type comments, omit source locations,
and cover all 12 files. Token comparisons retain string contents, code tokens,
indentation, and semantic newlines; ordinary comments and nonsemantic newlines
are excluded. Operational comments are compared separately.

The three physics doctest modules ran on Python 3.12.10: 19 examples, zero
failures. Manual review of the complete source diff found only intended comment
changes. No regression suite or new first-impact test was run or implemented.
Numpydoc lint and the final make_figures/baseline comparison remain pending.

The pre-existing staged evidence additions, four tracked helper deletions,
untracked reports/submission copies, and saved baseline evidence were preserved.
An aggregate SHA256 inventory of all other existing repository files and the
cached-diff hash matched their pre-edit values. No files were staged or committed.
Preserve the complete Assignment 3 transcript.
