"""Provide the command-line entry point for the native circle simulator.

Notes
-----
Running this file exits with main's returned status. Help and argument
errors raise SystemExit during parsing, before rendering is imported.
Importing the module does not open a GUI.
"""

import sys

from cli import parse_args
from state import PhysicsParameters


def main(argv=None) -> int:
    """Parse simulator options and launch the blocking native GUI.

    Parsing finishes before the renderer is imported. This permits help and
    invalid-option checks in a process that never opens a native window.

    Parameters
    ----------
    argv : list of str or None, optional
        Arguments excluding the executable name; None uses process arguments.
        Options select restitution (default 0.8) and dt (default 1/240 s).

    Returns
    -------
    int
        0 after normal GUI completion, or 1 after RenderingDependencyError.

    Raises
    ------
    SystemExit
        Parsing exits with 0 for help or 2 for invalid arguments.
    Exception
        Unexpected parameter, import, or rendering errors propagate.

    See Also
    --------
    cli.parse_args : Validate the command-line options.

    Notes
    -----
    Creates physical parameters, imports rendering after successful parsing,
    and calls run_simulation. Missing rendering dependencies are printed to
    stderr and converted to return code 1. The renderer owns GUI resources
    and prints startup/shutdown information. See assign3/SPEC.md [EQ-STEP].

    Examples
    --------
    Help can be inspected without opening a window.

    >>> import contextlib, io
    >>> from main import main
    >>> output = io.StringIO()
    >>> with contextlib.redirect_stdout(output):
    ...     try:
    ...         main(['--help'])
    ...     except SystemExit as exc:
    ...         status = exc.code
    >>> (status, '--restitution' in output.getvalue())
    (0, True)
    """
    args = parse_args("Real-time circle simulation in an open box.", argv)
    parameters = PhysicsParameters(restitution=args.restitution, dt=args.dt)
    # Help and invalid options finish before the rendering module is imported.
    from rendering import RenderingDependencyError, run_simulation

    try:
        run_simulation(parameters)
    except RenderingDependencyError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
