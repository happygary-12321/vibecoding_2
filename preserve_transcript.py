"""Copy the actual Codex JSONL transcript intact; never reconstruct messages."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DEFAULT_SOURCE = Path("D:/CodexCLI/data/sessions/2026/10/01/rollout-2026-10-01T21-07-30-01a0fa26-efc6-7f61-9193-fb16ebf88047.jsonl")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--final", action="store_true",
                        help="user confirms this export covers the whole task through the last review")
    args = parser.parse_args()
    raw = args.source.read_bytes()
    records = [json.loads(line) for line in raw.decode("utf-8").splitlines() if line.strip()]
    meta = next(r["payload"] for r in records if r["type"] == "session_meta")
    if Path(meta["cwd"]).resolve() != ROOT:
        parser.error("session cwd does not match this project")
    messages = [r for r in records if r["type"] == "response_item" and r["payload"].get("role") == "user"]
    if not any("For this first task, work strictly in planning/read-only mode." in json.dumps(r) for r in messages):
        parser.error("the original task was not found; inspect transcript coverage")
    models = sorted({r["payload"]["model"] for r in records
                     if r["type"] == "turn_context" and "model" in r["payload"]})
    directory = ROOT / "docs" / "transcript"
    directory.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    destination = directory / f"snapshot-{stamp}-{args.source.name}"
    destination.write_bytes(raw)
    manifest = dict(source=str(args.source), file=destination.name,
                    sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw),
                    session_id=meta["id"], originator=meta.get("originator"),
                    cli_version=meta.get("cli_version"), source_interface=meta.get("source"),
                    models=models, records=len(records), user_messages=len(messages),
                    first_record=records[0].get("timestamp"), last_record=records[-1].get("timestamp"),
                    last_user_record=messages[-1].get("timestamp"),
                    final_coverage_confirmed_by_user=args.final)
    (directory / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
