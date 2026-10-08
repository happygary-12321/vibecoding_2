"""Provide the command-line entry point for headless figures and evidence.

Notes
-----
Running this file exits with main's returned status. Importing it does
not generate figures. Execution can overwrite the selected output files;
see validation.run_validation and assign3/SPEC.md Section 6.
"""

import sys

from cli import parse_args
from validation import run_validation


def main(argv=None) -> int:
    """Parse experiment options, generate evidence, and return a status code.

    Parameters
    ----------
    argv : list of str or None, optional
        Arguments excluding the executable name; None uses process arguments.
        Defaults: restitution 0.8, dt 1/240 s, duration 1 s, bounce duration
        10 s, and output directory 'figures'.

    Returns
    -------
    int
        0 for a passed report; 1 for a failed report or caught OSError.

    Raises
    ------
    SystemExit
        Parsing exits with 0 for help or 2 for invalid options/durations.
    Exception
        Errors not converted to a failed report or caught as OSError
        propagate, including errors while formatting a malformed report.

    Notes
    -----
    Calls run_validation, which creates directories and overwrites PNG,
    JSON and regression output. Prints successful numerical summaries to
    stdout, or failure diagnostics to stderr. An experiment exception caught
    inside run_validation is reported as a failed report, not re-raised here.
    No GUI is opened. See assign3/SPEC.md [EQ-DRIFT] and [EQ-ACCOUNTING].
    """
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
