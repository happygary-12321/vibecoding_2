# Original transcript and submission packaging

The snapshot JSONL in this directory is a byte-for-byte copy of the actual Codex
session log, not a reconstruction from summaries. `manifest.json` records its
source, byte count, SHA-256, session metadata, model IDs, and coverage timestamps.
The original source remains intact at:

```text
D:\CodexCLI\data\sessions\2026\10\01\rollout-2026-10-01T21-07-30-01a0fa26-efc6-7f61-9193-fb16ebf88047.jsonl
```

It contains the original planning prompt and subsequent work. The session is still
ongoing, so the current snapshot does not claim final coverage. After final review,
refresh locally with Python 3.12.10; older snapshots remain intact:

```text
python preserve_transcript.py
```

Inspect the newest snapshot and confirm that it includes the final assistant reply
and user review. Only then use the following flag to record that actual confirmation:

```text
python preserve_transcript.py --final
```

If the session log moved, supply `--source "absolute\path\to\original.jsonl"`.
Do not replace the raw export with an index or edited narrative. The report records
the snapshot used at build time; a later final snapshot may extend it, and the
manifest always identifies the latest snapshot. Rebuild and review the PDF if you
want the final snapshot hash in the report itself.

## Final package

After successful final checks, actual reflection/root-cause review, PDF visual QA,
and complete transcript confirmation, run:

```text
python package_submission.py
```

This refuses to overwrite an existing archive. A later package can use
`--output submission\HW2_submission_v2.zip`. It includes the correct main working
tree (including reviewed, as-yet-uncommitted documentation), report.pdf, all evidence,
raw transcripts, the Word template, and the actual full `.git` directory. Both
local bug branches and their committed reproducible helpers remain in that Git
history. Extra readable helper copies are included under `experiments/` in the ZIP.
It excludes linked experiment worktrees, virtual environments, caches, temporary
Word files, unrelated test.txt, temporary PDF files, and submission archives.
The script performs archive CRC checking and creates a file/hash manifest.
It does not commit, push, merge, or call git archive.

Before submission, extract into a new directory and check `git log`, `git branch`,
the PDF, transcript manifest, evidence, and helper availability. The copied full
`.git` retains worktree-registration metadata with paths on the original machine;
these paths may not be usable after relocation. Keep the original repository
untouched. In the EXTRACTED COPY ONLY, inspect `git worktree list` and, if those
paths are stale, use `git worktree prune --expire now` before recreating worktrees.
Branch refs and commits remain preserved. To reproduce in that extracted copy:

```text
git worktree add .bug-worktrees\explicit-euler bug/explicit-euler
git worktree add .bug-worktrees\unconditional-restitution bug/unconditional-restitution
```

Run each committed experiment helper from its respective worktree with `--help`
and supply `--main-dir` pointing to the extracted correct main directory. Evidence
reruns may replace existing experiment output files; retain the submitted archive
unchanged as the original evidence. Never merge defects or push either bug branch.
