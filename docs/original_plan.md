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
