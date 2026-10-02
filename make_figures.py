"""Run deterministic numerical checks and write headless validation figures."""

import sys

from cli import parse_args
from validation import run_validation


def main(argv=None) -> int:
    args = parse_args("Headless numerical validation and PNG figures.", argv, figures=True)
    try:
        report = run_validation(args.output_dir, args.restitution, args.dt,
                                args.duration, args.bounce_duration)
    except OSError as exc:
        print(f"Cannot write validation evidence: {exc}", file=sys.stderr)
        return 1
    if report["status"] != "passed":
        print(f"Validation FAILED. See {args.output_dir}/results.json and regression_checks.txt.",
              file=sys.stderr)
        for check in report["checks"]:
            if not check["passed"]:
                print(f"  {check}", file=sys.stderr)
        if "exception" in report:
            print(report["exception"], file=sys.stderr)
        return 1
    print(f"Validation passed. Figures and numerical evidence saved in {args.output_dir}.")
    for label, run in zip(("coarse", "fine"), report["free_fall"]):
        row = run["final"]
        print(f"{label}: y={row['y']:.12g} m (expected {row['expected_height']:.12g}); "
              f"vy={row['vy']:.12g} m/s (expected {row['expected_vy']:.12g}); "
              f"signed error={row['signed_error']:.12g} m "
              f"(expected {row['predicted_signed_error']:.12g})")
    for label, run in zip(("selected", "elastic"), report["bouncing"]):
        print(f"{label}: e={run['parameters']['restitution']}, impacts={run['impact_counts']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
