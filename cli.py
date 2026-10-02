"""Shared command-line parsing, independent of physics and rendering."""

import argparse
import math


def finite_number(text: str) -> float:
    """Parse a finite floating-point number with an argparse-friendly error."""
    try:
        value = float(text)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be a number") from exc
    if not math.isfinite(value):
        raise argparse.ArgumentTypeError("must be finite")
    return value


def restitution_value(text: str) -> float:
    value = finite_number(text)
    if not 0.0 <= value <= 1.0:
        raise argparse.ArgumentTypeError("must be between 0 and 1 inclusive")
    return value


def timestep_value(text: str) -> float:
    value = finite_number(text)
    if value <= 0.0:
        raise argparse.ArgumentTypeError("must be greater than zero seconds")
    return value


def parse_args(description: str, argv=None, *, figures=False) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=description,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--restitution", type=restitution_value, default=0.8,
        help="coefficient of restitution, finite and in [0, 1]",
    )
    parser.add_argument(
        "--dt", type=timestep_value, default=1.0 / 240.0,
        help="fixed physics timestep in seconds, finite and positive (1/240 s by default)",
    )
    if figures:
        parser.add_argument("--output-dir", default="figures", help="directory for PNG and JSON results")
        parser.add_argument("--duration", type=timestep_value, default=1.0,
                            help="free-fall duration in seconds, positive and aligned with dt")
        parser.add_argument("--bounce-duration", type=timestep_value, default=10.0,
                            help="bouncing duration in seconds, positive and aligned with dt")
    args = parser.parse_args(argv)
    if figures:
        from validation import validate_experiments

        try:
            validate_experiments(args.dt, args.duration, args.bounce_duration)
        except ValueError as exc:
            parser.error(str(exc))
    return args
