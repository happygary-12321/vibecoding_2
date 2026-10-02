# Stage 6 requirement audit

Baseline inspected: `71834cd` on `main`; the local origin/main reference also
points there. Initial status: only Simulator_Report_Template.docx untracked.
Existing source, original plan, figures, and template were not modified by this audit.

Status meanings: **repository verified** means inspected files/history, not a fresh
runtime test; **user-reported** means a statement supplied in the conversation;
**pending** means evidence or a deliverable is still outstanding.

| Requirement | Status and evidence |
|---|---|
| Original plan verbatim | Repository verified: docs/original_plan.md contains the original response. Git diff from documentation baseline 14da723 to HEAD is empty. Keep it unchanged for Appendix A. |
| Two real changes and reasons | Repository verified: docs/change_log.md records revised git/review workflow and contact-direction diagnostic, with the user's reasons. |
| Final file layout | Production inventory below plus Stage 6 additions below. Report builder emits one line per actual included file at generation time. |
| main.py | Implementation present. User reports local GUI works correctly and accepted Stage 5. Specific changed-parameter, camera interaction, and shutdown observations are not separately documented. |
| make_figures.py | Implementation and saved outputs present. Existing results.json reports passed, Agg backend, and no rendering/PyVista imports. Fresh final rerun pending. |
| Restitution and dt options | Present in shared CLI and passed to physics; CLI verification was supplied by the user in Stage 1. Current final CLI rerun pending. |
| Six meaningful commits | Repository verified: 14da723 documentation; 94e2e4f CLI; 1c9fdce integration; a5f5654 contacts; 9e0e842 validation; 71834cd rendering. Additional dependency and setup commits also exist. No empty commits counted. |
| Required validation figures | Agent visually inspected all four tracked PNGs and both actual bug plots. Saved results inspected; fresh final runtime rerun pending. |
| Two evidenced bugs | Complete measured intentional cases in docs/bug_cases.md. A: 2246cdccb68777de4f97c8800debd2ecff9ab82c; B: 12880a10f2640f74404fca08491608bf94809d1a. Both user-run faulty suites exited 1 and correct-main reruns exited 0. Evidence under evidence/bug_a and evidence/bug_b. |
| Prompting reflection | Editable draft in docs/report.md; personal wording and root-cause wording await user review. |
| Actual tool/model | Authoritative raw session metadata: Codex, codex-tui 0.157.0, source vscode, provider openai, turn_context model gpt-6-astra. See docs/provenance.md. |
| Complete transcript | Actual original JSONL copied byte-for-byte under docs/transcript; manifest records SHA-256 and coverage. Current session continues: final refresh and user coverage confirmation remain pending. |
| report.pdf | Editable docs/report.md and build_report.py prepared. PDF generation and all-page visual QA pending local execution. No PDF is claimed generated. |
| Repository archive including .git | package_submission.py prepared; execution/inspection pending final evidence and review. Includes actual .git and both local bug branches/helpers; excludes linked experiment worktrees, caches, venvs, Word temporary files, unrelated test.txt, and archives. |

## Existing numerical evidence (read, not rerun by this agent)

Source: tracked figures/results.json and figures/regression_checks.txt. The JSON
does not record the execution commit, so do not assign it an exact run SHA.
The artifacts are present in the accepted 71834cd tree.

- Python 3.12.10; Matplotlib 3.10.7; NumPy 2.3.5; backend Agg.
- 26 top-level checks report passed; 11 regression tests report OK.
- Coarse final height: 5.074562500000006 m; vy: -9.80999999999998 m/s;
  signed height error: -0.02043749999999367 m.
- Fine final height: 5.084781250000005 m; vy: -9.809999999999963 m/s;
  signed height error: -0.010218749999994614 m.
- Maximum total energy-accounting residual: 7.39630579005279e-13 J for
  selected restitution, 8.26005930321116e-14 J for the elastic diagnostic.
- Actual installed PyVista/VTK versions and final dependency consistency are pending.

## Current file inventory (one line per project file)

```text
.gitignore — exclusions, including local experiment worktrees.
README.md — setup, commands, architecture, and verification instructions.
main.py — real-time simulation entry point.
make_figures.py — headless validation/figure entry point.
cli.py — shared validated command-line options.
state.py — SI-unit dataclasses and validation.
integration.py — contact-free and complete physics steps.
contacts.py — floor/wall responses and contact records.
rendering.py — PyVista scene and fixed-step real-time scheduler.
validation.py — deterministic experiments, energy accounting, plots, and JSON.
check_cli.py — CLI and headless output checks.
check_integration.py — integration and state checks.
check_contacts.py — contact and complete-step checks.
check_scheduling.py — synthetic-time scheduler checks.
requirements.txt — complete dependency list.
requirements-figures.txt — plotting dependency list.
requirements-rendering.txt — rendering dependency list.
docs/original_plan.md — unchanged original planning response.
docs/change_log.md — two approved revisions and their reasons.
docs/provenance.md — known tool/model and transcript provenance.
docs/submission_audit.md — this audit and outstanding evidence.
docs/bug_cases.md — pre-experiment hypotheses and later measured bug evidence.
figures/free_fall.png — height and signed-error plot.
figures/free_fall_energy.png — numerical energy-drift plot.
figures/bouncing_energy.png — bouncing energy and accounting plots.
figures/contact_direction.png — correct versus illustrative faulty contact rule.
figures/results.json — existing numerical traces, checks, and environment.
figures/regression_checks.txt — existing integration/contact test output.
Simulator_Report_Template.docx — existing user-provided report template, preserved untracked.
```

The actual .git directory must be included in the eventual submission archive,
but its internal files are repository metadata, not source modules. Ignored
test.txt, Word temporary files, and caches are not submission files.

## Stage 6 additions and verification checkpoint

```text
build_report.py - expands editable report and generates PDF with original-plan attachment.
final_verify.py - captures all final check outputs, versions, and exit codes.
preserve_transcript.py - copies actual raw session bytes and records coverage/hash.
package_submission.py - packages actual .git, source, report, evidence, and transcript.
requirements-report.txt - ReportLab and pypdf dependencies.
docs/report.md - editable report with measured evidence and reflection draft.
docs/report_review.json - outstanding user review and PDF-hash confirmation.
docs/transcript/README.md - raw transcript refresh and packaging instructions.
docs/transcript/manifest.json - snapshot provenance and SHA-256.
docs/transcript/snapshot-*.jsonl - original raw session log bytes, not reconstructed prose.
evidence/bug_a/comparison_results.json - measured trajectories, outcomes, versions, and SHAs.
evidence/bug_a/explicit_euler_comparison.png - inspected actual-module signed-height plot.
evidence/bug_b/comparison_results.json - measured signed responses, outcomes, versions, and SHAs.
evidence/bug_b/unconditional_restitution_comparison.png - inspected actual-module signed-velocity plot.
```

Both evidence directories also preserve full test logs, separate exit-code files,
defect.diff, experiment_commit.txt, and helper-run output. The original recorded
hypotheses in docs/bug_cases.md remain unchanged. Helpers are committed on their
respective faulty branches, retained locally and in the eventual full .git copy.

Agent checks: inspected Git history/worktrees and measured artifacts; visually
inspected six PNGs; production diff against 71834cd is empty; git diff --check
reports no whitespace errors (only Windows line-ending notices). No Python
runtime checks or PDF generation have been executed in this agent session.

Pending user-local checks: run final_verify.py, generate report.pdf with
build_report.py, inspect all PDF pages, review reflection/root-cause wording,
refresh and confirm complete transcript coverage, then package and inspect the
archive. No final main commit or push has been made. Word template preserved.
