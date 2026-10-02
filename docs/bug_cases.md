# Bug case studies — evidence in progress

No adequately evidenced real implementation bugs have been found in the current
repository or supplied conversation. Git write permissions, interpreter discovery,
and dependencies are environment issues, not physics bugs. The illustrative
faulty series already in figures/contact_direction.png is not branch evidence.

Predicted faulty values below remain **predictions until measured output exists**.
Setup and baseline evidence are distinguished from pending faulty-run evidence below.
Main must retain the accepted production functions. Do not push faulty branches.

### Setup attempt (agent session)

After recording the hypothesis below, the agent ran:
`git worktree add -b bug/explicit-euler .bug-worktrees/explicit-euler 71834cd`.
It exited 1: `fatal: cannot lock ref 'refs/heads/bug/explicit-euler': unable to
create directory for .git/refs/heads/bug/explicit-euler`.
Subsequent `git branch --list` and `git worktree list` showed only main at
71834cd and the original worktree. No injection or experiment ran. This is a Git
write restriction, not a bug case. Local setup and baseline output are required
before continuing.

### Confirmed local setup and Bug A preparation

The subsequent repository inspection confirmed main and the existing
bug/explicit-euler worktree at 71834cd71e46266ee11339df18d1a891d5e7151b.
The user-created evidence/bug_a/baseline_before.txt reports Python 3.12.10,
five passing integration tests, and baseline_before.exit.txt contains 0.
This is a verified saved local-run artifact, not an agent-executed Python test.

After that inspection, the agent changed only the integration update order in
the experiment worktree and added bug_a_experiment.py there. No detecting
assertions changed. The actual uncommitted production diff is saved under
evidence/bug_a/defect.diff. Main integration/state/contacts/check_integration
have an empty diff against 71834cd. Whitespace review reported no errors.

The helper requires a committed experiment on bug/explicit-euler, captures the
existing failing check's complete stdout/stderr and exit code, and loads the
correct integration.py directly from the accepted Git commit. Both plotted
numerical series come from actual step functions. It reruns correct-main checks
and saves all generated evidence under evidence/bug_a. The helper itself is kept
only in the experiment worktree/branch. Faulty commit SHA, helper execution,
measured failures, plot review, and post-experiment baseline pass were pending at
that preparation checkpoint. The measured record below supersedes that status.

## A. Deliberately injected explicit Euler (pre-experiment record)

- Correct starting baseline: 71834cd.
- Proposed local branch: bug/explicit-euler.
- Proposed worktree: .bug-worktrees/explicit-euler.
- Hypothesis recorded before injection: moving the gravity update after position
  updates will use the old vertical velocity and reverse the signed height error.
- Proposed mutation: in integration.step, update x and y first, then vy, preserving
  the step-count increment. Do not change analytic references or detecting checks.
- Predicted one-second result at dt=1/240: y=5.1154375 m, vy=-9.81 m/s,
  error=+0.0204375 m instead of expected y=5.0745625 m and error=-0.0204375 m.
- Predicted detection: check_integration.py fails its one-step and signed-error
  checks; make_figures.py returns nonzero and plots the trajectory from the actual
  mutated step against unchanged semi-implicit reference lines. Its numeric checks
  collect failures without intentionally stopping plot generation.
- Evidence required: branch and commit SHA, defect.diff, full test log and exit
  code, make_figures log/exit code, actual free_fall.png/results.json, and a passing
  integration rerun on unchanged main. Store outputs outside accepted figures/.
- Symptom: pending measured failure; do not substitute the predicted value.
- Root cause draft for user review: position uses the pre-gravity velocity rather
  than the required updated velocity, changing the integration scheme. This is a
  deliberately injected rule violation, not a discovered historical defect.
- Prevention: signed-error and one-step regression checks; successful main rerun pending.

### A. Measured case study — deliberately injected, not a historical defect

**Provenance.** Local branch bug/explicit-euler, faulty commit
2246cdccb68777de4f97c8800debd2ecff9ab82c, correct baseline
71834cd71e46266ee11339df18d1a891d5e7151b. The user executed the experiment locally
under Python 3.12.10. The agent inspected the resulting files and PNG; it did not
execute these Python tests. Original pre-injection hypotheses above are preserved.

**Symptom (observed).** At t=1 s, dt=1/240 s, y0=10 m, vy0=0, g=9.81 m/s^2:

| Quantity | Correct baseline measured | Faulty production module measured |
|---|---:|---:|
| Height (m) | 5.074562500000006 | 5.115437500000006 |
| Signed height error (m) | -0.02043749999999367 | +0.020437500000006104 |
| Vertical velocity (m/s) | -9.80999999999998 | -9.80999999999998 |

The analytical height is 5.095 m. Predictions were correct within the 1e-10
absolute tolerance: faulty height 5.1154375 m and error +0.0204375 m, versus
required semi-implicit height 5.0745625 m and error -0.0204375 m.
The existing suite ran five tests and failed two (exit 1):
test_free_fall_and_refinement and test_one_step. The former detected the wrong
error sign at the first timestep; the latter measured y=2.3 rather than 2.2019 m.

**Hypotheses.** The original pre-injection hypothesis was that moving gravity
after position would use old velocity and reverse the height-error sign. The
measured sign reversal, unchanged final velocity, and defect diff support it.

**Root cause — draft for user review in their own words.** Explicit Euler uses
the old vertical velocity for position, so it misses that step's gravity-induced
displacement. The assignment requires semi-implicit Euler, which uses the updated
velocity. The different accumulation produces equal-magnitude, opposite-sign
height errors in this constant-gravity case. This was deliberately introduced
on a separate branch; main did not need a production fix.

**Prevention and correct-baseline verification.** Keep the independent one-step
expectations and signed-error formula checks. evidence/bug_a/baseline_before.txt
and baseline_after.txt each record five passing tests with exit 0. The helper
also verified main source unchanged. Agent Git inspection confirms main remains
at 71834cd and the defect is isolated to its branch.

**Visual evidence reviewed.** The agent opened explicit_euler_comparison.png.
The height panel identifies the analytical reference and both actual production
modules with commit labels; the lower panel clearly shows the faulty positive
error and baseline negative error. Units, legends, and labels are readable. This
is accepted as usable agent-inspected visual evidence, not an assertion of an
additional user review decision.

**Evidence files.** Under evidence/bug_a: defect.diff, experiment_commit.txt,
faulty_integration_checks.txt and .exit.txt (1), baseline_after.txt and .exit.txt
(0), comparison_results.json, explicit_euler_comparison.png, experiment_run.txt
and .exit.txt (0), plus the original baseline_before files. The helper's exit 0
means intentional-defect detection succeeded; it does not mean faulty tests
passed. The reproducible helper is committed on the faulty branch. The experiment
used the dedicated comparison helper, not a claimed make_figures.py branch run.

## B. Deliberately injected unconditional floor restitution (pre-mutation record)

- Correct starting baseline: 71834cd, in its own separate local worktree/branch.
- Authorized local branch: bug/unconditional-restitution.
- Planned worktree: .bug-worktrees/unconditional-restitution.
- Hypothesis recorded before the second injection: removing the vy<0 guard
  reverses an already outward velocity during floor penetration correction.
- Controlled parameters: radius=0.2 m, y=0.15 m, vy=+2 m/s, restitution=0.8.
- Mutation scope: remove only the floor's inward-motion guard; preserve floor
  position correction, both wall rules, and all detecting assertions.
- Predicted result: y=0.15 m, vy=+2 m/s becomes y=0.2 m, vy=-1.6 m/s at e=0.8;
  correct behavior preserves vy=+2 m/s and marks no impact.
- Predicted detection: check_contacts.py outward/touching cases and the diagnostic
  assertions fail. A branch-specific diagnostic must plot the actual modified
  resolver response and explicitly label it as such. The existing illustrative
  faulty calculation alone is not valid evidence.
- Symptom, actual defect diff/SHA, measured values, failure logs, actual-resolver
  figure, and successful correct-main rerun: pending.
- Root cause draft for user review: penetration correction and inward-velocity
  response have different conditions; overlap alone does not justify reversal.
- Prevention: moving-away and touching regression cases; baseline rerun pending.

The Bug B comparison must run the actual faulty worktree resolver and load the
correct resolver from Git at baseline 71834cd, using identical controlled state.
Record signed before/after velocities, y corrections, and is_impact for each.
Capture existing contact-test output and exit code, committed diff and SHA,
JSON measurements, actual-resolver PNG, and passing main contact checks under
evidence/bug_b. Keep its reproducible helper on the isolated branch. Nothing in
this pre-mutation record claims that Bug B has run or that predictions were measured.

### B. Preparation checkpoint (no faulty-run results yet)

The existing bug/unconditional-restitution worktree was confirmed clean at
71834cd before mutation. The saved local baseline_before.txt reports six passing
contact tests; baseline_before.exit.txt contains 0. The agent then removed only
the floor vy<0 guard and added bug_b_experiment.py in that worktree. The exact
production diff is saved in evidence/bug_b/defect.diff. Side-wall rules,
integration, state, and detecting contact tests are unchanged. Main remains on
main at 71834cd with unchanged production functions. The helper is prepared to
load baseline contacts.py directly from Git, measure both actual resolvers,
capture failing tests and a passing-main rerun, and label its plot with actual
commits. Faulty branch commit, execution, measurements, and visual QA are pending.

### B. Measured case study - deliberately injected, not a historical defect

**Provenance.** Branch bug/unconditional-restitution, commit
12880a10f2640f74404fca08491608bf94809d1a, baseline
71834cd71e46266ee11339df18d1a891d5e7151b. The user ran the experiment locally
with Python 3.12.10; the agent inspected its saved output and PNG. Preparation
notes above describe the earlier checkpoint; this measured record supersedes
their pending status without rewriting the original predictions.

**Symptom and measurements.** With r=0.2 m, y=0.15 m, vy=+2 m/s, e=0.8, the
baseline resolver measured y=0.2 m, vy=+2 m/s, is_impact=False. The actual faulty
resolver measured y=0.2 m, vy=-1.6 m/s, is_impact=True. Both corrected y by
0.05000000000000002 m, preserved vx=1.5 m/s, and left step_count=0. These results
match the pre-mutation predictions within 1e-12 SI tolerance. The contact suite
ran six tests with two failing outward-floor subcases (penetrating and exactly
touching), exit 1; each found -1.6 versus expected +2 m/s, a 3.6 m/s difference.

**Hypotheses.** Before mutation, the recorded explanation was that removing the
vy<0 guard conflates overlap correction with inward impact response. The actual
floor-only diff and measured outward-to-inward reversal support that hypothesis.

**Root cause - draft for user review in their own words.** The code always
multiplies vy by -e on floor contact. That is valid only for inward motion.
An outward-moving overlapping circle still needs position correction, but its
velocity must be preserved. This condition was intentionally removed on a local
branch; side walls and main production code were not altered.

**Prevention.** Retain direction-specific regression cases for penetrating and
exactly touching states. The saved baseline_before and baseline_after contact
suites each passed all six tests, exit 0. The experiment confirms main source
matches baseline. The actual signed-velocity plot detects a change from upward
to downward directly; kinetic energy alone squares velocity and cannot uniquely
identify its sign. The positive-error plot for Bug A detects a different defect:
the integrator's order changes the sign of accumulated height error.

**Visual review.** The agent inspected
evidence/bug_b/unconditional_restitution_comparison.png. Commit labels identify
actual baseline 71834cd and faulty 12880a1 production resolvers. Before/after
labels, signed SI velocity axis, zero line, and corrected-position annotation are
readable. The faulty line crosses zero and ends at -1.6 m/s while baseline stays
at +2 m/s. It is usable actual-branch evidence, not the earlier illustrative plot.

**Evidence paths.** evidence/bug_b contains experiment_commit.txt, defect.diff,
faulty_contact_checks.txt and .exit.txt (1), baseline_before.txt and .exit.txt (0),
baseline_after.txt and .exit.txt (0), comparison_results.json,
unconditional_restitution_comparison.png, experiment_run.txt and .exit.txt (0).
Helper exit 0 confirms defect detection and baseline pass, not faulty-suite success.
bug_b_experiment.py is preserved in the faulty commit. Neither defect is merged
into main or authorized for push.
