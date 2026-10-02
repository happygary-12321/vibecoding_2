# Bouncing Circle Simulation

Review draft. Production baseline: 71834cd. Final regression rerun, report PDF generation, and PDF visual QA are pending. This report distinguishes inspected local evidence from tests executed by the agent.

## Part 1 - Plan review and architecture

The original plan was produced before implementation and is preserved unchanged in Appendix A. Two actual revisions were requested and approved before building.

Revision 1 replaced milestones reserved for later user revisions with substantive deliverables and required review of diffs and actual checks before accepting each commit. The user's reason was: "The assignment requires me to review and revise the plan before building. The commit history should represent substantive development work."

Revision 2 added a signed-velocity contact-direction diagnostic for a circle overlapping the floor while moving upward. The user's reason was: "The existing free-fall plot does not exercise contact, and energy alone does not show velocity direction. The assignment requires a plot that detects the deliberately introduced bug."

The production modules use meters, seconds, and kilograms. State, integration, contacts, and rendering are separate. PyVista, meshes, colors, camera, and display timing live only in rendering.py. There is no ceiling collision, friction, rotation, continuous collision detection, or resting-contact threshold.

```text
.gitignore - supporting source, documentation, or evidence
build_report.py - PDF report builder
check_cli.py - supporting source, documentation, or evidence
check_contacts.py - supporting source, documentation, or evidence
check_integration.py - supporting source, documentation, or evidence
check_scheduling.py - supporting source, documentation, or evidence
cli.py - shared CLI parsing
contacts.py - contact resolution and records
docs/bug_cases.md - supporting source, documentation, or evidence
docs/change_log.md - supporting source, documentation, or evidence
docs/original_plan.md - original plan unchanged
docs/provenance.md - supporting source, documentation, or evidence
docs/report.md - editable report narrative
docs/report_review.json - supporting source, documentation, or evidence
docs/submission_audit.md - supporting source, documentation, or evidence
docs/transcript/manifest.json - supporting source, documentation, or evidence
docs/transcript/README.md - supporting source, documentation, or evidence
docs/transcript/snapshot-20261002T0932437266802Z-rollout-2026-10-01T21-07-30-01a0fa26-efc6-7f61-9193-fb16ebf88047.jsonl - supporting source, documentation, or evidence
evidence/bug_a/baseline_after.exit.txt - supporting source, documentation, or evidence
evidence/bug_a/baseline_after.txt - supporting source, documentation, or evidence
evidence/bug_a/baseline_before.exit.txt - supporting source, documentation, or evidence
evidence/bug_a/baseline_before.txt - supporting source, documentation, or evidence
evidence/bug_a/comparison_results.json - supporting source, documentation, or evidence
evidence/bug_a/defect.diff - supporting source, documentation, or evidence
evidence/bug_a/experiment_commit.txt - supporting source, documentation, or evidence
evidence/bug_a/experiment_run.exit.txt - supporting source, documentation, or evidence
evidence/bug_a/experiment_run.txt - supporting source, documentation, or evidence
evidence/bug_a/explicit_euler_comparison.png - supporting source, documentation, or evidence
evidence/bug_a/faulty_integration_checks.exit.txt - supporting source, documentation, or evidence
evidence/bug_a/faulty_integration_checks.txt - supporting source, documentation, or evidence
evidence/bug_b/baseline_after.exit.txt - supporting source, documentation, or evidence
evidence/bug_b/baseline_after.txt - supporting source, documentation, or evidence
evidence/bug_b/baseline_before.exit.txt - supporting source, documentation, or evidence
evidence/bug_b/baseline_before.txt - supporting source, documentation, or evidence
evidence/bug_b/comparison_results.json - supporting source, documentation, or evidence
evidence/bug_b/defect.diff - supporting source, documentation, or evidence
evidence/bug_b/experiment_commit.txt - supporting source, documentation, or evidence
evidence/bug_b/experiment_run.exit.txt - supporting source, documentation, or evidence
evidence/bug_b/experiment_run.txt - supporting source, documentation, or evidence
evidence/bug_b/faulty_contact_checks.exit.txt - supporting source, documentation, or evidence
evidence/bug_b/faulty_contact_checks.txt - supporting source, documentation, or evidence
evidence/bug_b/unconditional_restitution_comparison.png - supporting source, documentation, or evidence
evidence/final/check_cli.exit.txt - supporting source, documentation, or evidence
evidence/final/check_cli.txt - supporting source, documentation, or evidence
evidence/final/check_contacts.exit.txt - supporting source, documentation, or evidence
evidence/final/check_contacts.txt - supporting source, documentation, or evidence
evidence/final/check_integration.exit.txt - supporting source, documentation, or evidence
evidence/final/check_integration.txt - supporting source, documentation, or evidence
evidence/final/check_scheduling.exit.txt - supporting source, documentation, or evidence
evidence/final/check_scheduling.txt - supporting source, documentation, or evidence
evidence/final/figures/bouncing_energy.png - supporting source, documentation, or evidence
evidence/final/figures/contact_direction.png - supporting source, documentation, or evidence
evidence/final/figures/free_fall.png - supporting source, documentation, or evidence
evidence/final/figures/free_fall_energy.png - supporting source, documentation, or evidence
evidence/final/figures/regression_checks.txt - supporting source, documentation, or evidence
evidence/final/figures/results.json - supporting source, documentation, or evidence
evidence/final/make_figures.exit.txt - supporting source, documentation, or evidence
evidence/final/make_figures.txt - supporting source, documentation, or evidence
evidence/final/pip_check.exit.txt - supporting source, documentation, or evidence
evidence/final/pip_check.txt - supporting source, documentation, or evidence
evidence/final/summary.json - supporting source, documentation, or evidence
evidence/stage6_review.diff - supporting source, documentation, or evidence
figures/bouncing_energy.png - supporting source, documentation, or evidence
figures/contact_direction.png - supporting source, documentation, or evidence
figures/free_fall.png - supporting source, documentation, or evidence
figures/free_fall_energy.png - supporting source, documentation, or evidence
figures/regression_checks.txt - supporting source, documentation, or evidence
figures/results.json - supporting source, documentation, or evidence
final_verify.py - final local check capture
integration.py - integration and complete step
main.py - real-time entry point
make_figures.py - headless entry point
package_submission.py - archive with actual .git
preserve_transcript.py - byte-preserved session export
README.md - supporting source, documentation, or evidence
rendering.py - PyVista and scheduling
requirements-figures.txt - supporting source, documentation, or evidence
requirements-rendering.txt - supporting source, documentation, or evidence
requirements-report.txt - supporting source, documentation, or evidence
requirements.txt - supporting source, documentation, or evidence
Simulator_Report_Template.docx - supporting source, documentation, or evidence
state.py - SI state and validation
validation.py - numerical experiments and figures
report.pdf - generated report (created by this build)
.git/ - complete repository metadata; both local bug commits and helpers remain here
```

## Part 2 - Implementation and reviewed milestones

Assignment parameters are radius 0.2 m, mass 1 kg, gravity 9.81 m/s^2, restitution 0.8, box width 4 m and displayed height 3 m, initial position (1, 2) m, velocity (1.5, 0) m/s, and dt=1/240 s.

Each complete step first updates vy using gravity, then updates x and y using the updated velocity, increments the integer step count once, and resolves floor/left/right contacts. Simulation time is step_count*dt. The contact-free integrator remains separately usable for numerical validation. Penetration is corrected for all contacts, but restitution changes normal velocity only when motion is into the surface. Corner components are handled independently.

The native PyVista timer drives display callbacks. A monotonic clock and accumulator feed fixed physics steps, capped at 60 per callback. Excess whole steps are discarded and recorded, while the fractional remainder is retained. Overload therefore makes simulation time lag wall time without changing dt. The scene is created once; the disk actor moves under a fixed orthographic camera.

Meaningful main-history milestones (verified in Git):

- 14da723: preserved plans, provenance, and development workflow.
- 94e2e4f: validated CLI scaffold and checks.
- 1c9fdce: physics state and semi-implicit Euler integration.
- a5f5654: floor and side-wall contacts.
- 9e0e842: headless validation and figures.
- 38cd01e: dependency update.
- 71834cd: PyVista rendering and fixed-step scheduling.

The conversation records staged user acceptance. The user performed local Python runs and commits because this agent session could not execute the installed Python interpreter or write Git metadata. Those environment restrictions are not physics bugs. The user reports that the Stage 5 GUI works correctly; detailed changed-parameter and shutdown observations are not independently claimed here. The agent inspected source diffs, saved numerical evidence, and PNG figures.

## Part 3 - Numerical validation and interpretation

Existing figures/results.json records Python 3.12.10, Matplotlib 3.10.7, NumPy 2.3.5, Agg backend, 26 passing numerical checks, and 11 passing integration/contact regression tests. These are saved local-run artifacts, not tests run in the agent session. The artifacts do not identify their original execution commit; they are present in the accepted baseline. Final rerun status is reported separately below.

Free fall starts at y0=10 m from rest with surfaces distant. The exact reference is y0 - g*t^2/2. Semi-implicit Euler gives signed height error -g*dt*t/2 at matching step times. The negative sign means the numerical height is below the analytical height. Halving dt halves the first-order error.

At one second, analytical height is 5.095 m. Measured coarse height is 5.074562500000006 m and error is -0.02043749999999367 m; measured fine height is 5.084781250000005 m and error is -0.010218749999994614 m. Measured vertical velocities are approximately -9.81 m/s. Maximum signed-error residuals are about 6.33e-15 m and 8.24e-15 m, within the 1e-10 m tolerance.

![Figure 1. Measured height and signed error for dt and dt/2; the reference error lines overlap the measured errors.](figures/free_fall.png)

Mechanical energy uses the circle center: E=m*(vx^2+vy^2)/2 + m*g*y. A contact-free semi-implicit step changes energy by -m*g^2*dt^2/2. Over time t, the drift is -m*g^2*dt*t/2. This is integration error, not physical dissipation. Expected one-second drift is -0.200491875 J for dt and -0.1002459375 J for dt/2; saved residuals are below 3.22e-13 J versus a 1e-9 J tolerance.

![Figure 2. Contact-free numerical energy drift agrees with its derived reference and decreases with timestep refinement.](figures/free_fall_energy.png)

At inward impacts, restitution removes normal kinetic energy: delta K=-m*(1-e^2)*vn_before^2/2. Correcting floor penetration raises potential energy by m*g*dy. This position-correction contribution is a numerical artifact, distinct from physical restitution loss. Contact records separate these contributions without duplicating the production integrator.

The 10-second bouncing runs use e=0.8 and e=1. The elastic run has zero restitution loss but still exhibits integration drift and position-correction jumps. It does not perfectly conserve energy. Maximum total-accounting residuals in the saved results are 7.40e-13 J and 8.26e-14 J, both below 1e-9 J.

Late in the dissipative run, many small floor responses remain. Gravity applied each fixed step followed by penetration correction and restitution can sustain a small discrete bounce cycle. No resting threshold was requested, so this behavior is retained rather than silently changing the contact rule. Dense impact markers do not establish exact physical rest.

![Figure 3. Total energy and separate cumulative contributions for dissipative and elastic runs. Floor and wall markers use actual velocity-changing contact records.](figures/bouncing_energy.png)

The standard contact-direction figure is a controlled illustration. It uses the correct resolver and an isolated faulty comparison. It is not itself evidence of a mutated production branch; Part 4 supplies that evidence.

![Figure 4. Original headless contact-direction illustration, clearly labeled as not an injected branch run.](figures/contact_direction.png)

Final local-run record: commit 71834cd71e46266ee11339df18d1a891d5e7151b; Python 3.12.10. All commands passed: True. check_integration exit 0; check_contacts exit 0; check_scheduling exit 0; check_cli exit 0; make_figures exit 0; pip_check exit 0. Installed versions: {"matplotlib": "3.10.7", "numpy": "2.3.5", "pypdf": "6.19.0", "pyvista": "0.49.0", "reportlab": "5.0.1", "vtk": "9.7.1"}. These logs were generated by local execution, not by the agent's inspection.

## Part 4 - Two deliberately injected physics defects

No adequately evidenced historical implementation defects were found. Both cases below were intentionally introduced on separate local branches from 71834cd. Main's production code was not changed. Complete pre-mutation hypotheses, logs, diffs, and measured evidence are retained in docs/bug_cases.md and evidence/.

Bug A: explicit Euler. Branch bug/explicit-euler, commit 2246cdccb68777de4f97c8800debd2ecff9ab82c. The pre-mutation hypothesis predicted a positive rather than negative height error when position uses old velocity. The measured faulty endpoint is 5.115437500000006 m with signed error +0.020437500000006104 m. The correct baseline produces 5.074562500000006 m and negative error. Both final vertical velocities remain approximately -9.81 m/s.

The existing integration suite failed two of five tests, exit 1: the one-step position and free-fall signed-error checks. The main rerun passed five tests, exit 0. Root cause draft: the order of operations changes the numerical method even though the same gravity and dt are used. Prevention is the independently calculated one-step and signed-error regression checks. The signed-height plot separates the methods much more clearly than height alone.

![Figure 5. Bug A actual faulty and correct production modules, identified by commit; the lower panel reveals the wrong error sign.](evidence/bug_a/explicit_euler_comparison.png)

Bug B: unconditional floor restitution. Branch bug/unconditional-restitution, commit 12880a10f2640f74404fca08491608bf94809d1a. The recorded hypothesis predicted that removing the inward-motion condition would reverse an already upward velocity. With radius=0.2 m, y=0.15 m, vy=+2 m/s, e=0.8, both actual resolvers measured corrected y=0.2 m. The correct resolver preserved vy=+2 m/s and is_impact=False; the faulty resolver produced vy=-1.6 m/s and is_impact=True.

The existing contact suite ran six tests and reported two failing subcases for outward floor motion, exit 1. Main's rerun passed all six tests, exit 0. Root cause draft: position correction and velocity response require different conditions; overlap alone is insufficient for reflection. Prevention is regression coverage for penetrating and exactly touching states moving away from each surface. A signed velocity diagnostic directly detects the reversal; kinetic energy alone cannot uniquely identify direction because it squares velocity.

![Figure 6. Bug B actual production resolvers loaded from the faulty and accepted commits. The zero line makes the erroneous direction reversal explicit.](evidence/bug_b/unconditional_restitution_comparison.png)

Both experiment helpers returned 0 because deliberate-defect detection and correct-main reruns succeeded. Their faulty test suites separately returned 1. The helpers are committed on their respective local branches and preserved in .git; neither faulty branch should be pushed or merged.

## Part 5 - Tool provenance and prompting reflection

Actual session metadata identifies Codex (originator codex-tui, version 0.157.0, source vscode, provider openai) and model gpt-6-astra in turn_context records. The identifier is read from the original log, not guessed. See docs/provenance.md. Raw transcript snapshot: docs/transcript/snapshot-20261002T0932437266802Z-rollout-2026-10-01T21-07-30-01a0fa26-efc6-7f61-9193-fb16ebf88047.jsonl; SHA-256 5b1136d493bdd1b098b25388ca78861f4a1db64bae2b29e4655985efb4b537b7. Final coverage confirmed by user: False.

Reflection draft for the student's review, not a claimed personal reflection: Specific prompts made the update order, collision direction condition, and module boundaries testable. Requiring a plan revision before implementation linked the requested changes to concrete checks. Stage-by-stage review and recoverable commits made it possible to isolate deliberate faults without damaging the accepted simulator. The main limitation was that local execution and GUI observation depended on the user, so the report must separate observed artifacts from checks the agent could not run. The signed diagnostics provided stronger evidence than a visually plausible animation alone.

The student should revise this paragraph into their own words and add only observations they actually made. Exact model provenance, transcript coverage, final verification, and PDF visual QA must be resolved or explicitly disclosed before submission.

## Appendix A - Original plan, unchanged

The following appendix reproduces the original Markdown source literally, preserving its wording, equations, and formatting characters rather than rewriting the plan. Visual line wrapping is for page layout only. The exact source file is also embedded in the PDF as original_plan.md and included in the submission.

This is the proposed original implementation plan. No files will be created or modified, and no implementation will begin until you review it.

1. **Proposed file and module layout**

   ```text
   main.py — Parse options and run the real-time simulation through the rendering module.
   make_figures.py — Run deterministic checks headlessly and save validation plots and numerical results.
   state.py — Define physics parameters, box geometry, and mutable circle state in SI units.
   integration.py — Implement semi-implicit Euler integration and compose one complete physics step.
   contacts.py — Resolve floor and side-wall contacts, penetration, and restitution.
   rendering.py — Own all PyVista objects, camera settings, visual styling, and real-time scheduling.
   cli.py — Define shared command-line options and validate their values.
   validation.py — Define numerical experiments, assertions, reference values, and plotting routines.
   requirements.txt — Record the dependencies needed for rendering, plotting, and report generation.
   README.md — Document setup, commands, controls, module responsibilities, and validation outputs.
   .gitignore — Exclude caches and reproducible temporary outputs.
   docs/original_plan.md — Preserve this approved original plan verbatim.
   docs/change_log.md — Record your requested changes, your reasons, and their implementation status.
   docs/bug_cases.md — Record real or deliberately introduced bugs and the checks that detect them.
   docs/provenance.md — Record the actual coding tool, available model identity, environment, and transcript source.
   docs/report.md — Maintain the report text and figure references.
   docs/transcript/ — Store complete exported conversation records with an index of their coverage.
   figures/ — Store generated validation plots and machine-readable results.
   build_report.py — Convert the report source and preserved plan into report.pdf.
   report.pdf — Final submission report, visually inspected after generation.
   ```

   The physics remains three small modules: state, integration, and contacts. Rendering and validation may depend on physics; physics must never import either.

2. **State representation and module responsibilities**

   Use simple dataclasses rather than a general simulation framework:

   - `CircleState`: center position `x, y`, velocity `vx, vy`, and integer step count.
   - `PhysicsParameters`: radius, mass, gravity magnitude, restitution, and fixed timestep.
   - `Box`: width and height, with boundaries at `x = 0`, `x = width`, and `y = 0`.

   Defaults are radius `0.2 m`, mass `1.0 kg`, gravity `9.81 m/s²`, restitution `0.8`, width `4 m`, height `3 m`, position `(1.0, 2.0) m`, velocity `(1.5, 0.0) m/s`, and timestep `1/240 s`.

   Compute simulation time as `step_count × dt`, avoiding cumulative floating-point time addition.

   `contacts.py` will optionally return small contact records containing surface name, penetration correction, and normal velocity before and after response. These support validation without adding plotting or rendering concerns to physics.

   There will be no rotation, friction, ceiling collision, air resistance, or resting-contact threshold in the initial implementation.

3. **Exact order of operations for one physics step**

   For a timestep \(h\):

   1. Update velocity: \(v_x\) stays unchanged and \(v_y \leftarrow v_y-gh\).
   2. Update position using the new velocity: \(x \leftarrow x+v_xh\), \(y \leftarrow y+v_yh\).
   3. Resolve floor contact.
   4. Resolve left-wall contact.
   5. Resolve right-wall contact.
   6. Increment the step count and return any contact records.

   Contact rules:

   | Surface | Contact condition | Position correction | Velocity response |
   |---|---|---|---|
   | Floor | \(y \le r\) | Set \(y=r\) | If \(v_y<0\), set \(v_y=-ev_y\) |
   | Left wall | \(x \le r\) | Set \(x=r\) | If \(v_x<0\), set \(v_x=-ev_x\) |
   | Right wall | \(x \ge W-r\) | Set \(x=W-r\) | If \(v_x>0\), set \(v_x=-ev_x\) |

   Tangential velocity is unchanged. Penetration is corrected even when the circle is already moving away; that outward velocity is preserved.

   A floor-and-wall corner contact applies both independent normal responses. Nothing checks the upper boundary.

4. **Real-time rendering strategy**

   Render a filled disk centered on the physics position, with visible floor and side walls. Use a fixed orthographic camera looking directly along the z-axis at the x–y plane, with positive y upward. Disable camera interaction that would change this view.

   Treat `3 m` as the displayed box height. Show any upper extent marker as a clearly non-colliding dashed guide, subject to your review.

   Use a monotonic wall clock and a time accumulator:

   - Add elapsed wall time on each display callback.
   - Advance physics in fixed increments of `dt` while sufficient accumulated time remains.
   - Update the disk actor and render once per display callback.
   - Initially display the latest completed physics state without interpolation.

   Limit catch-up work to 60 physics steps per display callback. If more complete steps remain after that limit, discard the excess whole-step backlog, preserve the fractional remainder, and record the discarded wall time. The simulation then slows relative to wall time during overload; it never changes the physics timestep or takes a large catch-up step.

   Numerical experiments bypass this scheduler and execute an exact number of steps. Closing the window stops the callback and exits cleanly.

5. **CLI parameter validation**

   Both entry points will support:

   - `--restitution`, default `0.8`.
   - `--dt`, default `1/240`.
   - Descriptive `--help` output with units and defaults.

   `make_figures.py` will additionally accept `--output-dir` and a positive experiment duration.

   Reject nonnumeric or nonfinite values, timestep values at or below zero, and restitution outside `[0, 1]`. Reject invalid durations before starting experiments.

   Validate the internal configuration as well: positive radius and mass, positive box dimensions, width and height greater than the diameter, finite state values, and nonnegative gravity.

   Do not reject an initial center above the displayed height because there is no ceiling. Direct contact tests may intentionally start with penetration.

   For fixed-duration comparisons, require duration divided by timestep to be an integer within floating-point rounding tolerance. Explain invalid combinations and suggest an aligned duration; do not silently use a shortened final step. The default validation duration will be `1 s`, giving 240 and 480 steps.

   Import PyVista only through the rendering path so `make_figures.py` can run without opening or initializing a GUI.

6. **Numerical experiments, figures, and expected results**

   Run every assertion before reporting validation success. Save numerical results with the parameters used. Failed checks produce a nonzero exit status and a clear description.

   **Free fall and timestep refinement**

   Use \(y_0=10\text{ m}\), \(v_y=0\), \(v_x=0\), and a wide, tall box with the circle centered horizontally. Over one second, all contact surfaces remain safely distant.

   Run at \(h=1/240\) and \(h/2=1/480\). Record the initial sample and every completed step. Compare coarse samples with every second fine sample.

   Check:

   \[
   y_{\mathrm{exact}}(t)=y_0-\tfrac12gt^2
   \]

   \[
   y_{\mathrm{numeric}}(t)-y_{\mathrm{exact}}(t)
   =-\tfrac12ght
   \]

   At \(t=1\text{ s}\), expected values are:

   | Quantity | Expected value |
   |---|---:|
   | Exact height | `5.095 m` |
   | Height at `dt = 1/240 s` | `5.0745625 m` |
   | Signed error at `dt` | `−0.0204375 m` |
   | Height at `dt/2` | `5.08478125 m` |
   | Signed error at `dt/2` | `−0.01021875 m` |
   | Final vertical velocity for both runs | `−9.81 m/s` |

   Save a figure containing height versus time and signed error versus time, including the predicted error lines. Verify that halving the timestep halves the error at matching nonzero times.

   **Energy between and during impacts**

   Define mechanical energy using the circle center:

   \[
   E=\tfrac12m(v_x^2+v_y^2)+mgy.
   \]

   For a contact-free semi-implicit Euler step:

   \[
   E_{n+1}-E_n=-\tfrac12mg^2h^2.
   \]

   Therefore, free-fall energy drift after time \(t\) should be:

   \[
   E(t)-E(0)=-\tfrac12mg^2ht.
   \]

   At one second, the default coarse run should lose `0.200491875 J` numerically; the fine run should lose half that amount.

   Run the assignment’s bouncing configuration for 10 simulated seconds and plot energy versus time, marking floor and side-wall impacts. Also run an elastic diagnostic with restitution `1`.

   Record energy at three stages: before integration, after integration but before contacts, and after contact resolution. Account separately for:

   - Integration drift.
   - Normal kinetic energy removed by restitution:
     \[
     \Delta K=-\tfrac12m(1-e^2)(v_n^-)^2.
     \]
   - Potential-energy change caused by floor penetration correction:
     \[
     \Delta U=mg(y_{\mathrm{corrected}}-y_{\mathrm{penetrating}}).
     \]

   This prevents numerical position correction from being mislabeled as physical impact loss. With `e = 1`, restitution removes no kinetic energy, but timestep and position-correction artifacts can remain.

   **Contact checks**

   Test contact resolution directly, independently of integration:

   - Floor: `y = 0.15 m`, `vy = −2 m/s` becomes `y = 0.2 m`, `vy = +1.6 m/s`.
   - Left wall: `x = 0.15 m`, `vx = −2 m/s` becomes `x = 0.2 m`, `vx = +1.6 m/s`.
   - Right wall: `x = 3.85 m`, `vx = +2 m/s` becomes `x = 3.8 m`, `vx = −1.6 m/s`.
   - Penetrating but moving away: correct position and preserve velocity.
   - Exactly touching: reflect only inward velocity; preserve outward and zero normal velocity.
   - Corner contact: correct both coordinates and apply restitution to both inward components.
   - Restitution `0` and `1`: verify zero and unchanged reflected normal speed respectively.
   - Above the displayed box height: verify that no ceiling response occurs.
   - Full-step checks: confirm gravity and integration precede contact resolution.

   Check that tangential components are unchanged and resolved positions satisfy the allowed floor and wall bounds.

   **Tolerances**

   For short, direct contact cases, use absolute tolerances of `1e−12` in the relevant SI unit. For the default one-second trajectory and energy identities, use `1e−10 m`, `1e−10 m/s`, and `1e−9 J`.

   These tolerances allow floating-point roundoff while remaining many orders of magnitude below the expected discretization errors. Do not require the numerical trajectory itself to match the continuous solution within these tolerances; require its error to match the derived discrete formula.

   For substantially different user-selected durations or step counts, document a roundoff allowance scaled by problem magnitude and operation count. Do not loosen tolerances simply to make a failing check pass.

7. **Phased implementation and meaningful git milestones**

   After your review, inspect the workspace and preserve any existing work. Use an existing repository if present; otherwise initialize git before implementation.

   Each significant task starts from the previous verified commit. The initial bootstrap necessarily creates the first baseline. Before accepting each subsequent milestone, inspect the diff, run relevant checks, and record their actual outcomes.

   | Milestone | Meaningful committed result | Review and verification checkpoint |
   |---|---|---|
   | 1 | Original plan, provenance notes, project documentation, and executable CLI scaffold | Verify both help commands and honest “not implemented” behavior for unfinished paths |
   | 2 | Physics state and semi-implicit integration with initial free-fall checks | Verify velocity, position, sample times, and signed error |
   | 3 | Floor and side-wall contact handling with deterministic checks | Verify all response directions, penetration, corners, and restitution endpoints |
   | 4 | Complete headless validation entry point and figures | Run all checks; inspect plotted values and energy accounting |
   | 5 | PyVista rendering and fixed-step scheduling | Run a GUI smoke test; check camera, geometry, shutdown, and slow-frame behavior |
   | 6 | Your first requested revision | Record your reason; review the diff and run affected checks |
   | 7 | Your second requested revision | Record your reason; review the diff and run affected checks |
   | 8 | Completed bug evidence, report, transcript index, and reproducibility instructions | Run final checks, inspect report pages, review final diff and repository status |

   Milestones 6 and 7 depend on actual requests from you. They will not be fabricated to meet the commit count. Substantive fixes may add further commits. No empty commits or cosmetic splitting will be used.

8. **Bug evidence and deliberate-bug branches**

   When a real bug occurs, preserve the failing command, relevant parameters, expected and observed values, diagnostic output, affected commit, fix diff, and successful rerun. Record the explanation while the evidence is available.

   Do not retroactively describe an unobserved defect as a real bug.

   If fewer than two real bugs occur, create enough deliberately faulty cases on separate branches from a known passing baseline. Candidate faults are:

   - Change integration to update position before velocity. The signed free-fall error check should detect the wrong sign.
   - Apply restitution to a penetrating circle that is moving away. The outward-contact check should detect an incorrect velocity reversal.

   Commit each deliberate defect on its branch, run the existing detecting check, and preserve its nonzero exit result and output. Label it explicitly as an injected bug. Keep the branch and commit reference; do not merge the defect into the submission branch.

   Return to the clean baseline and rerun the detecting checks. Each case study will distinguish the failing branch from the correct submission behavior.

9. **Report and transcript preparation**

   Preserve this plan verbatim in `docs/original_plan.md` after implementation is authorized. Later changes belong in the change log; the original plan is not rewritten.

   Preserve complete conversation exports, including prompts, responses, and tool activity to the extent the application export provides them. Keep original exports intact and index their coverage. If complete export requires a manual action from you, identify that requirement early; do not reconstruct missing transcript content or claim a summary is complete.

   Record the coding tool from the actual environment and the model identifier only from authoritative session metadata. If the exact model identifier is unavailable, state that explicitly and request the displayed identifier or export metadata instead of inferring it.

   The report will contain:

   - The original plan verbatim.
   - At least two actual changes you requested and their stated reasons.
   - Final module layout and step order.
   - Validation methods, parameters, figures, actual results, and tolerances.
   - Two evidenced bug case studies, labeled real or deliberately injected.
   - A short reflection on numerical accuracy, contact artifacts, architecture, and the review process.
   - Tool/model provenance, commit references, and transcript location.

   Generate `report.pdf`, render its pages for visual inspection, and check equations, figure labels, page breaks, and the full original-plan text before delivery.

10. **Decisions for your review**

   The proposed defaults are:

   - Treat the box as open at the top, with a non-colliding upper extent guide.
   - Use discrete post-step penetration correction; do not add continuous collision detection.
   - Preserve the specified restitution rule without a resting-contact threshold, accepting possible small late-time bounces.
   - Cap real-time catch-up at 60 steps per callback and discard excess wall-time backlog.
   - Use a one-second free-fall experiment and a ten-second bouncing-energy experiment.
   - Keep physics dependencies minimal and use a compact assertion-based validation suite.
   - Require two genuine requested revisions before considering the report complete.

   Implementation is paused here for your review.

