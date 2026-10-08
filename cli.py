"""Parse shared simulator and headless-validation command-line options.

Notes
-----
Numeric arguments use ordinary scalar floats. Figure-mode parsing imports
validation to check durations; it does not run experiments or open a GUI.
Defaults and constraints are specified in assign3/SPEC.md Section 4.
"""

import argparse
import math


def finite_number(text: str) -> float:
    """Convert a command-line string to a finite float.

    Parameters
    ----------
    text : str
        Numeric literal accepted by float; expressions are not evaluated.

    Returns
    -------
    float
        Finite parsed scalar; units depend on the option using this parser.

    Raises
    ------
    argparse.ArgumentTypeError
        If float rejects the string or the parsed value is nonfinite.
    """
    try:
        value = float(text)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be a number") from exc
    if not math.isfinite(value):
        raise argparse.ArgumentTypeError("must be finite")
    return value


def restitution_value(text: str) -> float:
    """Parse a dimensionless restitution coefficient in the closed unit interval.

    Parameters
    ----------
    text : str
        Numeric command-line value.

    Returns
    -------
    float
        Finite scalar restitution in [0, 1].

    Raises
    ------
    argparse.ArgumentTypeError
        If parsing fails, the value is nonfinite, or it is outside [0, 1].

    Notes
    -----
    Both endpoints are accepted; see assign3/SPEC.md [EQ-NORMAL].
    """
    value = finite_number(text)
    if not 0.0 <= value <= 1.0:
        raise argparse.ArgumentTypeError("must be between 0 and 1 inclusive")
    return value


def timestep_value(text: str) -> float:
    """Parse a finite positive time value in seconds.

    Parameters
    ----------
    text : str
        Numeric command-line value for a timestep or duration.

    Returns
    -------
    float
        Finite scalar greater than zero, in s.

    Raises
    ------
    argparse.ArgumentTypeError
        If parsing fails or the value is nonfinite or nonpositive.
    """
    value = finite_number(text)
    if value <= 0.0:
        raise argparse.ArgumentTypeError("must be greater than zero seconds")
    return value


def parse_args(description: str, argv=None, *, figures=False) -> argparse.Namespace:
    """Parse shared options and optionally validate figure experiment durations.

    Parameters
    ----------
    description : str
        Description used in the help text.
    argv : list of str or None, optional
        Arguments excluding the executable name; None uses sys.argv[1:].
    figures : bool, optional
        False by default. If True, add output and duration options.

    Returns
    -------
    argparse.Namespace
        restitution (default 0.8) and dt (default 1/240 s). Figure mode
        also supplies output_dir ('figures'), duration (1 s), and
        bounce_duration (10 s). Numeric options are scalar floats.

    Raises
    ------
    SystemExit
        Status 0 for help, or 2 for parsing/range/duration errors.

    Notes
    -----
    May print help to stdout or errors to stderr. Restitution must be finite
    and in [0, 1]; times must be finite and positive. Figure durations must
    align to whole fixed steps within eight ulps, obey the per-run one-million
    step limit, and keep coarse free fall above the floor. Figure validation
    ValueError is converted to a parser error. No physics step or file write
    is performed. See assign3/SPEC.md [EQ-TIME] and Section 4.
    """
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
