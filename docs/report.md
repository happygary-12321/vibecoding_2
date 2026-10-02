# Bouncing Circle Simulation

Review draft. Production baseline: 71834cd. Final regression rerun, report PDF generation, and PDF visual QA are pending. This report distinguishes inspected local evidence from tests executed by the agent.

## Part 1 - Plan review and architecture

The original plan was produced before implementation and is preserved unchanged in Appendix A. Two actual revisions were requested and approved before building.

Revision 1 replaced milestones reserved for later user revisions with substantive deliverables and required review of diffs and actual checks before accepting each commit. The user's reason was: "The assignment requires me to review and revise the plan before building. The commit history should represent substantive development work."

Revision 2 added a signed-velocity contact-direction diagnostic for a circle overlapping the floor while moving upward. The user's reason was: "The existing free-fall plot does not exercise contact, and energy alone does not show velocity direction. The assignment requires a plot that detects the deliberately introduced bug."

The production modules use meters, seconds, and kilograms. State, integration, contacts, and rendering are separate. PyVista, meshes, colors, camera, and display timing live only in rendering.py. There is no ceiling collision, friction, rotation, continuous collision detection, or resting-contact threshold.

{{FILE_LAYOUT}}

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

{{FINAL_VERIFICATION}}

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

{{PROVENANCE}}

Reflection draft for the student's review, not a claimed personal reflection: Specific prompts made the update order, collision direction condition, and module boundaries testable. Requiring a plan revision before implementation linked the requested changes to concrete checks. Stage-by-stage review and recoverable commits made it possible to isolate deliberate faults without damaging the accepted simulator. The main limitation was that local execution and GUI observation depended on the user, so the report must separate observed artifacts from checks the agent could not run. The signed diagnostics provided stronger evidence than a visually plausible animation alone.

The student should revise this paragraph into their own words and add only observations they actually made. Exact model provenance, transcript coverage, final verification, and PDF visual QA must be resolved or explicitly disclosed before submission.

## Appendix A - Original plan, unchanged

The following appendix reproduces the original Markdown source literally, preserving its wording, equations, and formatting characters rather than rewriting the plan. Visual line wrapping is for page layout only. The exact source file is also embedded in the PDF as original_plan.md and included in the submission.

{{ORIGINAL_PLAN}}
