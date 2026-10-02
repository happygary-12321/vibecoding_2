# Approved plan revisions

The original plan is preserved unchanged in original_plan.md. Future work follows that plan with the following user-approved amendments. The later, explicit six-stage sequence below supersedes the original revision-reserved milestones.

## 1. Development and git workflow

User request: Integrate requested changes before implementation; remove milestones reserved for the user's first and second revisions. Organize meaningful commits around actual deliverables. After each significant task, show the diff and actual verification results, then wait for review before committing accepted changes as the baseline for the next task.

User reason: "The assignment requires me to review and revise the plan before building. The commit history should represent substantive development work."

Approved stages:
1. Project documentation, dependencies, and CLI scaffold.
2. Physics state and semi-implicit Euler integration.
3. Floor and side-wall contacts.
4. Headless validation and figures, including the contact-direction diagnostic.
5. PyVista rendering and fixed-step real-time scheduling.
6. Final verification and reproducibility documentation, including the report and bug evidence.

Use at least six meaningful commits. Start each significant task from an accepted committed baseline. Review actual diffs and verification results with the user before committing new implementation changes or starting the next stage. The user explicitly authorized creating and committing the initial documentation baseline before the Stage 1 scaffold. Preserve the configured remote and existing work; never force-push or upload an intentionally broken branch without explicit authorization.

## 2. Contact-direction diagnostic

User request: Headlessly plot vertical velocity before and after resolving a floor overlap with y=0.15 m, vy=+2 m/s, radius=0.2 m, and restitution=0.8. Correct handling changes y to 0.2 m and preserves vy=+2 m/s; the faulty rule changes vy to -1.6 m/s. Retain the regression assertion. Keep an injected production-code defect on a separate branch.

User reason: "The existing free-fall plot does not exercise contact, and energy alone does not show velocity direction. The assignment requires a plot that detects the deliberately introduced bug."

The plot will have before/after contact labels, a signed velocity axis with a zero line, correct and explicitly faulty series, and an annotation that both positions are corrected. The correct submission may include an isolated faulty comparison in validation code only. Actual injected production defects, their observed failures, and branch references must be preserved separately and never merged into the correct submission.

These are the two real requested revisions for the report; do not invent additional review decisions.
